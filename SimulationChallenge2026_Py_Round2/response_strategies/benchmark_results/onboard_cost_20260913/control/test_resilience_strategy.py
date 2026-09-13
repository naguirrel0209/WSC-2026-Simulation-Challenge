import datetime as dt
import math
from types import SimpleNamespace as NS
import pytest
import simulation_model
import scenario_builders
from maritime_data_context import Booking, Shipment, Demand
from response_strategies.resilience_strategy import ResilienceStrategy as S, _State, _commit, _FleetTransaction


def test_connection_buffer_and_rho():
    port, route = object(), object()
    state = _State()
    state.headways[route] = (20, 24)
    edge = NS(service_route=route, departure_port=port, total_distance=200)
    state.metrics[port] = (0.8, 8)
    assert math.isfinite(S._edge_cost(state, edge, True))
    low = S._edge_cost(state, edge, True)
    state.metrics[port] = (1, 8)
    assert S._edge_cost(state, edge, True) > low
    state.metrics[port] = (1, 8.01)
    assert math.isinf(S._edge_cost(state, edge, True))
    assert math.isfinite(S._edge_cost(state, edge, False))


def test_twcr_discharge_age_and_stable_tie(monkeypatch):
    import response_strategies.resilience_strategy as module
    now = dt.datetime(2026, 1, 10)
    old = NS(generated_time=now-dt.timedelta(days=5), teu_size=100)
    young = NS(generated_time=now-dt.timedelta(days=1), teu_size=100)
    a, b = object(), object()
    monkeypatch.setattr(module, '_work', lambda v,p: ([old], 10) if v is a else ([young], 1))
    port = NS(berths=[])
    # Hashable port object, like the actual domain Port.
    from maritime_data_context import Port
    port = Port('P')
    assert S.select_vessel_for_berth(object(), port, [a,b], [], now) is b
    assert S.select_vessel_for_berth(object(), port, [], [], now) is None


def test_bookings_connect_and_replace_reverse_references():
    c = scenario_builders.create_with_disruption()
    sim = simulation_model.Model(c, seed=2026)
    sim.run(duration=dt.timedelta(days=10))
    demand = c.demands[0]
    s = Shipment(demand=demand, teu_size=1)
    assert S.assign_associated_bookings(c, sim.clock_time, s)
    old = list(s.associated_bookings)
    assert S.assign_associated_bookings(c, sim.clock_time, s)
    assert s.current_booking_index == 1
    port = demand.origin_port
    for i,b in enumerate(s.associated_bookings,1):
        assert b.sequence_index == i
        segments = {x.sequence_index:x for x in b.service_route.segments}
        assert segments[b.departure_segment_index].associated_leg.departure_port is port
        port = segments[b.arrival_segment_index].associated_leg.arrival_port
        assert b in b.service_route.associated_bookings
    assert port is demand.destination_port
    assert all(b not in b.service_route.associated_bookings for b in old)
    assert not S.state(c).errors


def test_fleet_rollback_and_context_reset():
    c = scenario_builders.create_with_disruption()
    routes = list(c.service_routes)
    with pytest.raises(ValueError):
        with _FleetTransaction(c):
            c.service_routes.clear()
            raise ValueError('injected failure')
    assert c.service_routes == routes
    old = S.state(c)
    old.errors['x'] += 1
    assert not S.state(object()).errors


def test_missing_state_falls_back():
    assert S.assign_associated_bookings(object(), dt.datetime.min, None) is None
    assert S.create_alternative_service_routes(object(), dt.datetime.min) is True


@pytest.mark.parametrize('same_route', [True, False])
def test_rebooking_retains_current_index_and_references(monkeypatch, same_route):
    import response_strategies.resilience_strategy as module
    from maritime_data_context import Port, ServiceRoute, Segment, Leg, Vessel
    a,b,c = Port('A'),Port('B'),Port('C')
    route = ServiceRoute(id='R')
    segment = Segment(1, Leg(a,b,100), route)
    route.segments = [segment, Segment(2, Leg(b,c,100), route), Segment(3, Leg(c,a,100),route)]
    alternative = route if same_route else ServiceRoute(id='T')
    s = Shipment(teu_size=10, demand=Demand(origin_port=a,destination_port=c), generated_time=dt.datetime.min)
    original = Booking(1,s,route,1,2)
    s.associated_bookings, s.current_booking_index = [original], 1
    route.associated_bookings = [original]
    vessel = Vessel(assigned_service_route=route)
    vessel.current_segment, vessel.carried_shipments = segment,[s]
    edge = NS(service_route=alternative, departure_segment_index=2, arrival_segment_index=2)
    state = _State()
    monkeypatch.setattr(S,'_snapshot',classmethod(lambda cls,ctx,now:state))
    monkeypatch.setattr(S,'_path',classmethod(lambda cls,st,o,d:([edge],10)))
    monkeypatch.setattr(S,'_edge_cost',classmethod(lambda cls,st,e,t:10))
    monkeypatch.setattr(module,'_remaining_cost',lambda *args:1000)
    assert S.adjust_bookings_before_cargo_handling(object(),dt.datetime(2026,1,1),vessel)
    assert s.current_booking_index == 1
    assert original not in route.associated_bookings
    assert len(s.associated_bookings) == (1 if same_route else 2)
    assert s.get_current_booking().arrival_segment_index == (2 if same_route else 1)
    assert all(b in b.service_route.associated_bookings for b in s.associated_bookings)


def test_commit_failure_restores_state():
    from maritime_data_context import ServiceRoute
    class BrokenList(list):
        def append(self,value):
            raise ValueError('injected write failure')
    route = ServiceRoute(id='R')
    s = Shipment()
    old = Booking(1,s,route,1,2)
    s.associated_bookings, s.current_booking_index = [old],1
    route.associated_bookings = BrokenList([old])
    with pytest.raises(ValueError):
        _commit(s,[Booking(1,s,route,1,3)],1)
    assert s.associated_bookings == [old]
    assert route.associated_bookings == [old]
