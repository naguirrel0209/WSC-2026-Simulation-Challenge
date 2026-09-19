"""Static decision/contract tests: no Model construction or event execution."""
import datetime as dt
import math
from types import SimpleNamespace as NS

import pytest
import simulation_model  # Preserve the domain/engine's established import order.
from maritime_data_context import (
    Berth, Booking, Demand, Leg, MaritimeDataContext, Port, Segment,
    ServiceRoute, Shipment, Vessel, VesselClass,
)
from response_strategies.default_strategy import _CandidateBookingEdge as Edge
from response_strategies.h2_control_strategy import (
    ResilienceStrategy as Control, _State, _commit, _remaining_cost,
)
from response_strategies.h2_connection_strategy import H2ConnectionStrategy as H2

NOW = dt.datetime(2026, 1, 1)


def route(name, ports, distances):
    result = ServiceRoute(id=name)
    for i, distance in enumerate(distances, 1):
        leg = Leg(ports[i - 1], ports[i % len(ports)], distance)
        segment = Segment(i, leg, result)
        result.segments.append(segment)
        leg.segments.append(segment)
    return result


def state_for(ports, routes):
    state = _State()
    state.metrics = {p: (0.5, 0) for p in ports}
    state.headways = {r: (20, 24) for r in routes}
    return state


def assert_bookings(shipment, all_routes):
    port = shipment.demand.origin_port
    assert shipment.get_current_booking().sequence_index == shipment.current_booking_index
    for i, booking in enumerate(shipment.associated_bookings, 1):
        assert booking.sequence_index == i
        assert booking.shipment is shipment
        segments = {s.sequence_index: s for s in booking.service_route.segments}
        assert segments[booking.departure_segment_index].associated_leg.departure_port is port
        port = segments[booking.arrival_segment_index].associated_leg.arrival_port
        assert booking.service_route.associated_bookings.count(booking) == 1
    assert port is shipment.demand.destination_port
    for r in all_routes:
        assert all(b in shipment.associated_bookings for b in r.associated_bookings
                   if b.shipment is shipment)


def test_frequent_operational_connection_wins_over_slow_service():
    a, b, d = [Port(name) for name in ('Origin', 'Hub', 'Destination')]
    feeder = route('Feeder', [a, b], [100, 100])
    frequent, slow = [route(n, [b, d], [200, 200]) for n in ('Fast', 'Slow')]
    state = state_for([a, b, d], [feeder, frequent, slow])
    state.headways[frequent] = (20, 12)
    state.headways[slow] = (20, 48)
    state.metrics[b] = (0.8, 8)
    first = Edge(feeder, a, b, 1, 1, 100)
    fast = Edge(frequent, b, d, 1, 1, 200)
    last = Edge(slow, b, d, 1, 1, 200)
    state.edges = [first, fast, last]
    assert Control._path(state, a, d)[0] == [first, last]
    path, cost = H2._path(state, a, d)
    assert path == [first, fast]
    # 17 h feeder, then 10 sailing + 6 service + 8 port + 6 risk + 18 transfer.
    assert cost == pytest.approx(65)


@pytest.mark.parametrize('wait', [8, 8.01, 80])
def test_operational_connection_is_not_made_impossible_by_wait(wait):
    a, b = Port('A'), Port('B')
    r = route('R', [a, b], [200, 200])
    state = state_for([a, b], [r])
    state.metrics[a] = (1, wait)
    costs = []
    for headway in (12, 24, 48, 240):
        state.headways[r] = (20, headway)
        costs.append(H2._edge_cost(state, Edge(r, a, b, 1, 1, 200), True))
    assert all(math.isfinite(c) for c in costs)
    assert costs == sorted(costs)  # A frequent service cannot cost more for this reason.


@pytest.mark.parametrize('condition', ['departure_closed', 'arrival_closed', 'no_fleet', 'no_speed'])
def test_impossible_connection_has_no_path(condition):
    a, b, d = [Port(n) for n in ('A', 'B', 'D')]
    fast, safe = route('Fast', [a, b], [1, 1]), route('Safe', [a, d], [1000, 1000])
    state = state_for([a, b, d], [fast, safe])
    edge = Edge(fast, a, b, 1, 1, 1)
    if condition == 'departure_closed':
        state.metrics[a] = (1, math.inf)
    elif condition == 'arrival_closed':
        state.metrics[b] = (1, math.inf)
    elif condition == 'no_fleet':
        state.headways.pop(fast)
    else:
        state.headways[fast] = (0, 24)
    state.edges = [edge]
    assert math.isinf(H2._edge_cost(state, edge, True))
    assert H2._path(state, a, b) == (None, math.inf)


def rebooking_case(monkeypatch, *, remaining=1400, alternative=400, wait=8, rho=1):
    o, a, b, d = [Port(n) for n in ('Origin', 'A', 'Hub', 'Destination')]
    pre = route('Prefix', [o, a], [100, 100])
    current = route('Current', [a, b, d], [100, remaining, 100])
    other = route('Alternative', [b, d], [alternative, 100])
    shipment = Shipment(teu_size=10, demand=Demand(origin_port=o, destination_port=d))
    prefix, booking = Booking(1, shipment, pre, 1, 1), Booking(2, shipment, current, 1, 2)
    _commit(shipment, [prefix, booking], 2)
    vessel = Vessel(assigned_service_route=current)
    vessel.current_segment, vessel.carried_shipments = current.segments[0], [shipment]
    shipment.carrying_vessel = vessel
    state = state_for([o, a, b, d], [pre, current, other])
    state.metrics[b] = (rho, wait)
    state.edges = [Edge(current, b, d, 2, 2, remaining), Edge(other, b, d, 1, 1, alternative)]
    context = object()
    monkeypatch.setattr(H2, '_snapshot', classmethod(lambda cls, c, now: state))
    return NS(state=state, shipment=shipment, vessel=vessel, context=context, prefix=prefix,
              booking=booking, current=current, other=other, routes=[pre, current, other], b=b, d=d)


def test_full_first_transfer_cost_avoids_false_rebooking(monkeypatch):
    case = rebooking_case(monkeypatch)
    # Existing plan 70 + 12 + 8 = 90 h (H1 absent). Transfer 20+12+8+24+18 = 82 h.
    # The control's 58 h omits 24 h occupancy, incorrectly satisfying the 12 h gain.
    assert _remaining_cost(H2, case.state, case.shipment, case.booking,
                           case.vessel.current_segment) == 90
    assert H2.adjust_bookings_before_cargo_handling(case.context, NOW, case.vessel)
    assert case.shipment.associated_bookings == [case.prefix, case.booking]
    assert not H2.state(case.context).errors
    assert_bookings(case.shipment, case.routes)


def test_full_cost_participates_in_search_and_cache_key(monkeypatch):
    case = rebooking_case(monkeypatch, remaining=800)
    origin_path, origin_cost = H2._path(case.state, case.b, case.d)
    onboard_path, onboard_cost = H2._path(case.state, case.b, case.d,
                                        continuation=(case.current, 2))
    assert origin_path[0].service_route is case.other and origin_cost == 40
    assert onboard_path[0].service_route is case.current and onboard_cost == 60
    # Same OD but on the other service reverses the correct first-edge treatment.
    other_path, other_cost = H2._path(case.state, case.b, case.d, continuation=(case.other, 1))
    assert other_path[0].service_route is case.other and other_cost == 40
    assert H2._path(case.state, case.b, case.d) == (origin_path, origin_cost)


@pytest.mark.parametrize('distance, rebook', [(580, False), (560, True)])
def test_gain_boundary_and_transfer_counted_once(monkeypatch, distance, rebook):
    case = rebooking_case(monkeypatch, remaining=1360, alternative=distance, wait=4, rho=0.5)
    case.state.headways[case.current] = (20, 6)
    # Old=68+3+4=75; candidate 63 -> equality rejected, 62 -> accepted.
    assert H2.adjust_bookings_before_cargo_handling(case.context, NOW, case.vessel)
    assert (len(case.shipment.associated_bookings) == 3) is rebook
    assert case.shipment.associated_bookings[0] is case.prefix
    assert case.shipment.current_booking_index == 2
    assert case.shipment.carrying_vessel is case.vessel
    assert case.vessel.carried_shipments == [case.shipment]
    if rebook:
        assert case.booking not in case.current.associated_bookings
        assert case.shipment.get_current_booking().arrival_segment_index == 1
        assert case.shipment.associated_bookings[-1].service_route is case.other
    assert_bookings(case.shipment, case.routes)


def test_search_finds_second_connection_when_cheapest_is_impossible(monkeypatch):
    case = rebooking_case(monkeypatch, remaining=3000, alternative=1, wait=0, rho=0)
    backup = route('Backup', [case.b, case.d], [400, 400])
    case.routes.append(backup)
    case.state.headways[backup] = (20, 24)
    case.state.headways.pop(case.other)
    case.state.edges.append(Edge(backup, case.b, case.d, 1, 1, 400))
    assert H2.adjust_bookings_before_cargo_handling(case.context, NOW, case.vessel)
    assert case.shipment.associated_bookings[-1].service_route is backup
    assert_bookings(case.shipment, case.routes)


@pytest.mark.parametrize('headway', [24, 96, 240])
def test_h1_is_absent_and_s4_remaining_cost_wraps(headway):
    a, b, c = [Port(n) for n in ('Shanghai', 'Kaohsiung', 'Los Angeles')]
    s4 = route('S4', [a, b, c], [100, 200, 300])
    state = state_for([a, b, c], [s4])
    state.headways[s4] = (20, headway)
    shipment = Shipment(demand=Demand(origin_port=c, destination_port=b))
    booking = Booking(1, shipment, s4, 3, 1)
    _commit(shipment, [booking], 1)
    assert _remaining_cost(H2, state, shipment, booking, s4.segments[2]) == 5 + headway / 2
    assert _remaining_cost(H2, state, shipment, booking, s4.segments[0]) == 0


def test_future_transfer_cost_once_after_completed_current_booking(monkeypatch):
    case = rebooking_case(monkeypatch, alternative=400, wait=8, rho=1)
    case.booking.arrival_segment_index = 1
    future = Booking(3, case.shipment, case.other, 1, 1)
    _commit(case.shipment, [case.prefix, case.booking, future], 2)
    case.state.headways[case.other] = (20, 12)
    # Completed prefix/current contribute zero. 20+6+8+24+6+18 = 82.
    assert _remaining_cost(H2, case.state, case.shipment, case.booking,
                           case.vessel.current_segment) == 82
    assert H2._path(case.state, case.b, case.d, continuation=(case.current, 2))[1] == 82


def test_s4_same_vessel_continuation_merges_at_circular_index(monkeypatch):
    a, b, c = [Port(n) for n in ('Shanghai', 'Kaohsiung', 'Los Angeles')]
    s4 = route('S4', [a, b, c], [100, 200, 300])
    detour = route('Detour', [a, b], [3000, 3000])
    shipment = Shipment(demand=Demand(origin_port=c, destination_port=b))
    current, future = Booking(1, shipment, s4, 3, 3), Booking(2, shipment, detour, 1, 1)
    _commit(shipment, [current, future], 1)
    vessel = Vessel(assigned_service_route=s4)
    vessel.current_segment, vessel.carried_shipments = s4.segments[2], [shipment]
    state = state_for([a, b, c], [s4, detour])
    state.edges = [Edge(s4, a, b, 1, 1, 100)]
    monkeypatch.setattr(H2, '_snapshot', classmethod(lambda cls, ctx, now: state))
    assert H2.adjust_bookings_before_cargo_handling(object(), NOW, vessel)
    assert len(shipment.associated_bookings) == 1
    assert shipment.get_current_booking().departure_segment_index == 3
    assert shipment.get_current_booking().arrival_segment_index == 1
    assert current not in s4.associated_bookings and future not in detour.associated_bookings
    assert_bookings(shipment, [s4, detour])


def test_repeated_port_different_segment_is_a_transfer():
    a, b, c = [Port(n) for n in ('A', 'Hub', 'C')]
    r = route('Loop', [a, b, c, b], [100, 100, 100, 100])
    state = state_for([a, b, c], [r])
    edge = Edge(r, b, a, 4, 4, 100)
    state.edges = [edge]
    assert H2._path(state, b, a, continuation=(r, 2))[1] == 35
    assert H2._path(state, b, a, continuation=(r, 4))[1] == 17


@pytest.mark.parametrize('failure', [None, 'closed', 'fleet', 'slow'])
def test_real_snapshot_and_assignment_contracts_without_model(failure):
    context = MaritimeDataContext()
    a, b, d = [Port(n) for n in ('Origin', 'Hub', 'Destination')]
    context.ports = [a, b, d]
    for p in context.ports:
        p.berths = [Berth(1, p)]
    first, second = route('Feeder', [a, b], [100, 100]), route('Onward', [b, d], [200, 200])
    context.service_routes = [first, second]
    for r in context.service_routes:
        v = Vessel(assigned_service_route=r, vessel_class=VesselClass(sailing_speed=20))
        context.vessels.append(v)
        r.deployed_vessels.append(v)
        context.legs.extend(s.associated_leg for s in r.segments)
    if failure == 'closed':
        b.berths[0].is_available = False
    elif failure == 'fleet':
        second.deployed_vessels.clear()
    elif failure == 'slow':
        # Use the actual disruption-plan interface, without advancing time.
        from maritime_data_context import DisruptionPlan
        context.disruption_plans.append(DisruptionPlan(
            target_leg=second.segments[0].associated_leg,
            start_offset_days=(NOW - dt.datetime.min).days, duration_days=5, multiplier=5))
        second.segments[0].associated_leg.sailing_time_multiplier = 5
    shipment = Shipment(teu_size=1, demand=Demand(origin_port=a, destination_port=d))
    if failure:
        assert H2.assign_associated_bookings(context, NOW, shipment) is False
        assert not shipment.associated_bookings
    else:
        assert H2.assign_associated_bookings(context, NOW, shipment)
        old = list(shipment.associated_bookings)
        assert H2.assign_associated_bookings(context, NOW, shipment)
        assert shipment.current_booking_index == 1
        assert all(b not in b.service_route.associated_bookings for b in old)
        assert_bookings(shipment, context.service_routes)
    assert not H2.state(context).errors


def test_commit_failure_preserves_both_sides(monkeypatch):
    case = rebooking_case(monkeypatch, remaining=4000)
    class BrokenList(list):
        def append(self, value):
            raise ValueError('injected route append failure')
    case.other.associated_bookings = BrokenList()
    assert H2.adjust_bookings_before_cargo_handling(case.context, NOW, case.vessel) is None
    assert case.shipment.associated_bookings == [case.prefix, case.booking]
    assert case.shipment.current_booking_index == 2
    assert_bookings(case.shipment, case.routes)


def test_unrelated_policies_are_inherited_without_threshold_changes():
    for name in ('RHO_LIMIT', 'CONNECTION_BUFFER', 'FLEET_WAIT_HOURS', 'MIN_REBOOK_GAIN_HOURS'):
        assert getattr(H2, name) == getattr(Control, name)
    for name in ('select_vessel_for_berth', 'create_alternative_service_routes', '_snapshot'):
        assert getattr(H2, name).__func__ is getattr(Control, name).__func__
