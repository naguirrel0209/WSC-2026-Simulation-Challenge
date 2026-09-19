"""Decision and booking contracts on static objects; never advance a model."""
import datetime as dt
import math
from types import SimpleNamespace as NS

import pytest
import simulation_model
from maritime_data_context import (
    Berth, Booking, Demand, DisruptionPlan, MaritimeDataContext, Port,
    Segment, ServiceRoute, Shipment, Vessel, VesselClass,
)
from response_strategies import default_strategy as default
from response_strategies.h2_connection_strategy import H2ConnectionStrategy
from response_strategies.integrated_strategy import IntegratedStrategy as S, _candidate_edges, _travel_edge
from response_strategies.resilience_strategy import _State, _commit
from response_strategies.test_h2_connections import route, assert_bookings, NOW


def state_for(ports, routes, *, wait=0, rho=0.5):
    state = _State()
    state.metrics = {p: (rho, wait) for p in ports}
    state.headways = {r: (20, 24) for r in routes}
    state.edges = _candidate_edges(NS(service_routes=routes), state, ((), ()))
    return state


def context_for(ports, routes):
    context = MaritimeDataContext()
    context.ports, context.service_routes = ports, routes
    for port in ports:
        port.berths = [Berth(1, port)]
    for r in routes:
        vessel = Vessel(assigned_service_route=r, vessel_class=VesselClass(sailing_speed=20))
        r.deployed_vessels.append(vessel)
        context.vessels.append(vessel)
        for s in r.segments:
            if s.associated_leg not in context.legs:
                context.legs.append(s.associated_leg)
    return context


def test_operational_frequent_connection_beats_less_frequent_service():
    a, hub, d = [Port(n) for n in ('A', 'Hub', 'D')]
    feeder = route('Feeder', [a, hub], [100, 100])
    fast, slow = [route(n, [hub, d], [200, 200]) for n in ('Fast', 'Slow')]
    state = state_for([a, hub, d], [feeder, fast, slow])
    state.metrics[hub] = (0.8, 8)
    state.headways[fast], state.headways[slow] = (20, 12), (20, 48)
    path, cost = S._path(state, a, d)
    assert [e.service_route for e in path] == [feeder, fast]
    assert cost == pytest.approx(65)  # 17 feeder + 48 complete transfer.


@pytest.mark.parametrize('detour_leg, winner', [(300, 'Slow'), (100, 'Detour')])
def test_initial_booking_compares_slow_leg_with_real_detour_time(detour_leg, winner):
    a, x, d = [Port(n) for n in ('A', 'X', 'D')]
    slow = route('Slow', [a, d], [100, 100])
    slow.segments[0].associated_leg.sailing_time_multiplier = 5
    detour = route('Detour', [a, x, d], [detour_leg, detour_leg, 100])
    state = state_for([a, x, d], [slow, detour])
    path, _ = S._path(state, a, d)
    assert path[0].service_route.id == winner
    assert len(path) == 1


def test_weights_each_segment_once_and_preserves_physical_distances():
    a, b, c = [Port(n) for n in ('Shanghai', 'Kaohsiung', 'Los Angeles')]
    s4 = route('S4', [a, b, c], [100, 400, 300])
    s4.segments[0].associated_leg.sailing_time_multiplier = 5
    s4.segments[1].associated_leg.sailing_time_multiplier = 2
    state = state_for([a, b, c], [s4])
    edge = _travel_edge(state, s4, 0, 1)
    assert edge.total_distance == 500
    assert edge.weighted_distance == 1300
    assert S._edge_cost(state, edge, False) == 77  # 65 sailing + 12 service wait.
    assert [s.associated_leg.sailing_distance for s in s4.segments] == [100, 400, 300]
    # Third-to-first wraps S4, and the slow first segment is included once.
    wrapped = _travel_edge(state, s4, 2, 0)
    assert (wrapped.departure_segment_index, wrapped.arrival_segment_index) == (3, 1)
    assert wrapped.weighted_distance == 800
    assert S._edge_cost(state, wrapped, False, onboard=True) == 40


@pytest.mark.parametrize('closed_index', [0, 1, 2])
def test_closed_departure_intermediate_or_destination_is_impossible(closed_index):
    ports = [Port(n) for n in ('A', 'Hub', 'D')]
    r = route('R', ports, [100, 100, 100])
    state = state_for(ports, [r])
    state.metrics[ports[closed_index]] = (1, math.inf)
    assert _travel_edge(state, r, 0, 1) is None
    edges = _candidate_edges(NS(service_routes=[r]), state, ((), ()))
    assert not any(e.departure_port is ports[0] and e.arrival_port is ports[2] for e in edges)


def test_disconnected_segments_and_invalid_indices_are_not_bookings():
    a, b, c = [Port(n) for n in ('A', 'B', 'C')]
    r = route('R', [a, b, c], [100, 100, 100])
    state = state_for([a, b, c], [r])
    assert _travel_edge(state, r, -1, 1) is None
    assert _travel_edge(state, r, 0, 99) is None
    r.segments[1].associated_leg.departure_port = c
    assert _travel_edge(state, r, 0, 1) is None


@pytest.mark.parametrize('missing', ['fleet', 'speed'])
def test_snapshot_cannot_book_service_without_usable_fleet(missing):
    a, d = Port('A'), Port('D')
    r = route('R', [a, d], [100, 100])
    context = context_for([a, d], [r])
    if missing == 'fleet':
        r.deployed_vessels.clear()
    else:
        context.vessels[0].vessel_class.sailing_speed = 0
    shipment = Shipment(teu_size=1, demand=Demand(origin_port=a, destination_port=d))
    assert S.assign_associated_bookings(context, NOW, shipment) is False
    assert shipment.associated_bookings == []


def test_real_snapshot_books_slow_connection_and_replaces_reverse_references():
    a, b, d = [Port(n) for n in ('A', 'B', 'D')]
    feeder, onward = route('F', [a, b], [100, 100]), route('T', [b, d], [200, 200])
    context = context_for([a, b, d], [feeder, onward])
    leg = onward.segments[0].associated_leg
    leg.sailing_time_multiplier = 5
    context.disruption_plans = [DisruptionPlan(target_leg=leg,
        start_offset_days=(NOW - dt.datetime.min).days, duration_days=5, multiplier=5)]
    shipment = Shipment(teu_size=1, demand=Demand(origin_port=a, destination_port=d))
    assert S.assign_associated_bookings(context, NOW, shipment)
    old = list(shipment.associated_bookings)
    assert S.assign_associated_bookings(context, NOW, shipment)
    assert [b.service_route for b in shipment.associated_bookings] == [feeder, onward]
    assert all(b not in b.service_route.associated_bookings for b in old)
    assert_bookings(shipment, context.service_routes)
    assert not S.state(context).errors


def test_keeps_active_disruption_key_and_expires_alternative_within_cache_bucket():
    a, d = Port('A'), Port('D')
    original = route('R', [a, d], [100, 100])
    alt = ServiceRoute(id='ALT')
    alt.source_service_route = original
    alt.segments = [Segment(s.sequence_index, s.associated_leg, alt) for s in original.segments]
    stale = ServiceRoute(id='STALE')
    stale.source_service_route = original
    stale.segments = [Segment(s.sequence_index, s.associated_leg, stale) for s in original.segments]
    stale.disruption_key = ((), ())
    context = context_for([a, d], [original, alt, stale])
    leg = original.segments[0].associated_leg
    leg.sailing_time_multiplier = 5
    context.disruption_plans = [DisruptionPlan(target_leg=leg,
        start_offset_days=(NOW - dt.datetime.min).days, duration_days=0.01, multiplier=5)]
    key = default._get_active_disruption_key(context, NOW)
    assert key[1]  # A real congested leg is part of the identity.
    alt.disruption_key = key
    state = S._snapshot(context, NOW)
    assert any(e.service_route is alt for e in state.edges)
    assert not any(e.service_route is stale for e in state.edges)
    same = S._snapshot(context, NOW + dt.timedelta(minutes=1))
    assert same.edges is state.edges
    before_edges = state.edges
    # No event or model advance: only evaluate another supplied timestamp.
    expired = S._snapshot(context, NOW + dt.timedelta(minutes=15))
    assert expired.edges is not before_edges
    assert not any(e.service_route is alt for e in expired.edges)
    assert any(e.service_route is stale for e in expired.edges)


def test_multiplier_change_invalidates_costs_and_cached_choice():
    a, x, d = [Port(n) for n in ('A', 'X', 'D')]
    r = route('R', [a, d], [100, 100])
    detour = route('Detour', [a, x, d], [200, 200, 100])
    context = context_for([a, x, d], [r, detour])
    first = S._snapshot(context, NOW)
    assert S._path(first, a, d)[0][0].service_route is r
    r.segments[0].associated_leg.sailing_time_multiplier = 20
    second = S._snapshot(context, NOW)
    assert S._path(second, a, d)[0][0].service_route is detour
    r.segments[0].associated_leg.sailing_time_multiplier = 1
    restored = S._snapshot(context, NOW)
    assert S._path(restored, a, d)[0][0].service_route is r


def rebooking_case(monkeypatch, *, distance=300, multiplier=5, alternative=600, rho=0.5, wait=4):
    origin, a, hub, dest = [Port(n) for n in ('Origin', 'A', 'Hub', 'D')]
    pre = route('Prefix', [origin, a], [100, 100])
    current = route('Current', [a, hub, dest], [100, distance, 100])
    current.segments[1].associated_leg.sailing_time_multiplier = multiplier
    other = route('Other', [hub, dest], [alternative, 100])
    shipment = Shipment(teu_size=10, demand=Demand(origin_port=origin, destination_port=dest))
    prefix, booking = Booking(1, shipment, pre, 1, 1), Booking(2, shipment, current, 1, 2)
    _commit(shipment, [prefix, booking], 2)
    vessel = Vessel(assigned_service_route=current)
    vessel.current_segment, vessel.carried_shipments = current.segments[0], [shipment]
    shipment.carrying_vessel = vessel
    state = state_for([origin, a, hub, dest], [pre, current, other], wait=wait, rho=rho)
    context = object()
    monkeypatch.setattr(S, '_snapshot', classmethod(lambda cls, ctx, now: state))
    return NS(state=state, shipment=shipment, vessel=vessel, context=context, prefix=prefix,
              booking=booking, current=current, other=other, routes=[pre, current, other], hub=hub, dest=dest)


@pytest.mark.parametrize('alternative, should_rebook', [(900, False), (600, True)])
def test_onboard_slow_segment_only_diverts_when_full_transfer_pays_off(monkeypatch, alternative, should_rebook):
    case = rebooking_case(monkeypatch, alternative=alternative)
    assert S._remaining_cost(case.state, case.shipment, case.booking, case.vessel.current_segment) == 79
    assert S.adjust_bookings_before_cargo_handling(case.context, NOW, case.vessel)
    assert (len(case.shipment.associated_bookings) == 3) is should_rebook
    assert case.shipment.associated_bookings[0] is case.prefix
    assert case.shipment.current_booking_index == 2
    assert case.shipment.carrying_vessel is case.vessel
    assert case.vessel.carried_shipments == [case.shipment]
    if should_rebook:
        assert case.booking not in case.current.associated_bookings
        assert case.shipment.get_current_booking().arrival_segment_index == 1
        assert case.shipment.associated_bookings[-1].service_route is case.other
    else:
        assert case.shipment.associated_bookings == [case.prefix, case.booking]
    assert_bookings(case.shipment, case.routes)


def test_full_first_transfer_cost_prevents_false_gain_and_is_used_in_search(monkeypatch):
    case = rebooking_case(monkeypatch, distance=2000, multiplier=1, alternative=1000, rho=1, wait=8)
    assert S._remaining_cost(case.state, case.shipment, case.booking, case.vessel.current_segment) == 108
    path, cost = S._path(case.state, case.hub, case.dest, continuation=(case.current, 2))
    assert path[0].service_route is case.current and cost == 108
    # Transfer is 50 sailing + 12 service + 8 port + 24 occupancy + 18 = 112.
    transfer = _travel_edge(case.state, case.other, 0, 0)
    assert S._edge_cost(case.state, transfer, True) == 112
    assert S.adjust_bookings_before_cargo_handling(case.context, NOW, case.vessel)
    assert case.shipment.associated_bookings == [case.prefix, case.booking]


@pytest.mark.parametrize('headway', [24, 96, 240])
def test_h1_onboard_wait_consistent_for_current_plan_and_candidate(monkeypatch, headway):
    case = rebooking_case(monkeypatch)
    case.state.headways[case.current] = (20, headway)
    edge = _travel_edge(case.state, case.current, 1, 1)
    case.state.edges = [edge]
    assert S._remaining_cost(case.state, case.shipment, case.booking, case.vessel.current_segment) == 79
    assert S._path(case.state, case.hub, case.dest, continuation=(case.current, 2))[1] == 79
    assert S._path(case.state, case.hub, case.dest)[1] == 79 + headway / 2


def test_completed_current_booking_zero_and_future_connection_counted_once(monkeypatch):
    case = rebooking_case(monkeypatch, alternative=400, rho=1, wait=8)
    case.booking.arrival_segment_index = 1
    assert S._remaining_cost(case.state, case.shipment, case.booking, case.vessel.current_segment) == 0
    case.other.segments[0].associated_leg.sailing_time_multiplier = 2
    case.state.headways[case.other] = (20, 12)
    future = Booking(3, case.shipment, case.other, 1, 1)
    _commit(case.shipment, [case.prefix, case.booking, future], 2)
    # 40 sailing + 6 service + 8 port + 24 occupancy + 6 risk + 18 = 102.
    assert S._remaining_cost(case.state, case.shipment, case.booking, case.vessel.current_segment) == 102


def test_s4_wrap_and_same_vessel_merge_preserve_bookings(monkeypatch):
    a, b, c = [Port(n) for n in ('Shanghai', 'Kaohsiung', 'Los Angeles')]
    s4 = route('S4', [a, b, c], [100, 200, 300])
    s4.segments[0].associated_leg.sailing_time_multiplier = 5
    detour = route('Detour', [a, b], [3000, 3000])
    shipment = Shipment(demand=Demand(origin_port=c, destination_port=b))
    current, future = Booking(1, shipment, s4, 3, 3), Booking(2, shipment, detour, 1, 1)
    _commit(shipment, [current, future], 1)
    vessel = Vessel(assigned_service_route=s4)
    vessel.current_segment, vessel.carried_shipments = s4.segments[2], [shipment]
    state = state_for([a, b, c], [s4, detour])
    monkeypatch.setattr(S, '_snapshot', classmethod(lambda cls, ctx, now: state))
    assert S.adjust_bookings_before_cargo_handling(object(), NOW, vessel)
    assert len(shipment.associated_bookings) == 1
    merged = shipment.get_current_booking()
    assert (merged.departure_segment_index, merged.arrival_segment_index) == (3, 1)
    assert current not in s4.associated_bookings and future not in detour.associated_bookings
    assert S._remaining_cost(state, shipment, merged, s4.segments[2]) == 25
    assert_bookings(shipment, [s4, detour])


def test_rebooking_append_failure_is_atomic(monkeypatch):
    case = rebooking_case(monkeypatch)
    class BrokenList(list):
        def append(self, value):
            raise ValueError('injected write failure')
    case.other.associated_bookings = BrokenList()
    assert S.adjust_bookings_before_cargo_handling(case.context, NOW, case.vessel) is None
    assert case.shipment.associated_bookings == [case.prefix, case.booking]
    assert_bookings(case.shipment, case.routes)


def test_thresholds_and_fleet_berth_policies_remain_unchanged():
    for name in ('RHO_LIMIT', 'CONNECTION_BUFFER', 'FLEET_WAIT_HOURS', 'MIN_REBOOK_GAIN_HOURS'):
        assert getattr(S, name) == getattr(H2ConnectionStrategy, name)
    for name in ('select_vessel_for_berth', 'create_alternative_service_routes'):
        assert getattr(S, name).__func__ is getattr(H2ConnectionStrategy, name).__func__
