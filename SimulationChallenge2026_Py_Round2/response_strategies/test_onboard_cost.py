"""Onboard-cost regression tests using static domain objects, without a model run."""
import datetime as dt
import math

import pytest
import simulation_model  # Use the engine's normal import order.
from maritime_data_context import Booking, Demand, Leg, Port, Segment, ServiceRoute, Shipment, Vessel
from response_strategies.default_strategy import _CandidateBookingEdge
from response_strategies.resilience_strategy import _State, _commit, _remaining_cost
from response_strategies.user_strategy import UserStrategy as S


def _route(name, ports, distances):
    route = ServiceRoute(id=name)
    for index, distance in enumerate(distances, 1):
        leg = Leg(ports[index - 1], ports[index % len(ports)], distance)
        segment = Segment(index, leg, route)
        route.segments.append(segment)
        leg.segments.append(segment)
    return route


@pytest.fixture
def voyage():
    ports = [Port(name) for name in ('Shanghai', 'Kaohsiung', 'Los Angeles')]
    route = _route('S4', ports, [100, 200, 300])
    state = _State()
    state.headways[route] = (20, 96)
    state.metrics = {port: (0.5, 4) for port in ports}
    shipment = Shipment(teu_size=10, demand=Demand(origin_port=ports[0], destination_port=ports[2]))
    current = Booking(1, shipment, route, 1, 2)
    _commit(shipment, [current], 1)
    return state, ports, route, shipment, current


@pytest.mark.parametrize('headway', [24, 96, 240])
def test_onboard_continuation_does_not_depend_on_service_frequency(voyage, headway):
    state, ports, route, shipment, current = voyage
    state.headways[route] = (20, headway)
    assert _remaining_cost(S, state, shipment, current, route.segments[0]) == pytest.approx(14)
    edge = _CandidateBookingEdge(route, ports[1], ports[2], 2, 2, 200)
    assert S._edge_cost(state, edge, False) == pytest.approx(14 + headway / 2)


def test_onboard_continuation_keeps_port_wait(voyage):
    state, ports, route, shipment, current = voyage
    state.metrics[ports[1]] = (1, 30)
    assert _remaining_cost(S, state, shipment, current, route.segments[0]) == pytest.approx(40)


def test_remaining_cost_wraps_three_segment_s4_cycle(voyage):
    state, _, route, shipment, current = voyage
    current.departure_segment_index, current.arrival_segment_index = 2, 1
    assert _remaining_cost(S, state, shipment, current, route.segments[2]) == pytest.approx(9)


def test_completed_current_booking_has_no_remaining_cost(voyage):
    state, _, route, shipment, current = voyage
    assert _remaining_cost(S, state, shipment, current, route.segments[1]) == 0


@pytest.mark.parametrize('finished_current', [False, True])
def test_future_booking_keeps_wait_and_transfer_cost(voyage, finished_current):
    state, ports, route, shipment, current = voyage
    destination = Port('Destination')
    onward = _route('Onward', [ports[2], destination], [400, 400])
    state.headways[onward] = (20, 48)
    state.metrics[ports[2]] = (0.9, 8)
    state.metrics[destination] = (0, 0)
    future = Booking(2, shipment, onward, 1, 1)
    _commit(shipment, [current, future], 1)
    shipment.demand.destination_port = destination
    segment = route.segments[1 if finished_current else 0]
    # Future booking: 20 sailing + 24 service wait + 8 port wait + 12 rho + 18 transfer.
    assert _remaining_cost(S, state, shipment, current, segment) == pytest.approx(
        82 + (0 if finished_current else 14)
    )


@pytest.mark.parametrize('obstruction', ['closed', 'congested', 'no_speed', 'invalid_index'])
def test_existing_infeasibility_rules_remain(voyage, obstruction):
    state, ports, route, shipment, current = voyage
    if obstruction == 'closed':
        state.metrics[ports[2]] = (1, math.inf)
    elif obstruction == 'congested':
        route.segments[1].associated_leg.sailing_time_multiplier = 5
    elif obstruction == 'no_speed':
        state.headways.pop(route)
    else:
        current.arrival_segment_index = 99
    assert math.isinf(_remaining_cost(S, state, shipment, current, route.segments[0]))


@pytest.mark.parametrize('alternative_distance, should_rebook', [(600, False), (100, True)])
def test_rebooking_requires_real_gain_and_preserves_completed_prefix(
    monkeypatch, alternative_distance, should_rebook
):
    origin, a, b, destination = [Port(name) for name in ('Origin', 'A', 'B', 'Destination')]
    prefix_route = _route('Prefix', [origin, a], [100, 100])
    route = _route('Current', [a, b, destination], [100, 1200, 100])
    alternative = _route('Alternative', [b, destination], [alternative_distance, 100])
    shipment = Shipment(teu_size=10, demand=Demand(origin_port=origin, destination_port=destination))
    prefix = Booking(1, shipment, prefix_route, 1, 1)
    current = Booking(2, shipment, route, 1, 2)
    _commit(shipment, [prefix, current], 2)
    vessel = Vessel(assigned_service_route=route)
    vessel.current_segment, vessel.carried_shipments = route.segments[0], [shipment]
    shipment.carrying_vessel = vessel
    state = _State()
    state.headways = {route: (20, 96), alternative: (20, 24)}
    state.metrics = {port: (0.5, 4) for port in (origin, a, b, destination)}
    state.edges = [
        _CandidateBookingEdge(route, b, destination, 2, 2, 1200),
        _CandidateBookingEdge(alternative, b, destination, 1, 1, alternative_distance),
    ]
    monkeypatch.setattr(S, '_snapshot', classmethod(lambda cls, context, now: state))
    context = object()
    assert S.adjust_bookings_before_cargo_handling(context, dt.datetime(2026, 1, 1), vessel)
    assert not S.state(context).errors
    assert shipment.current_booking_index == 2
    assert shipment.associated_bookings[0] is prefix
    assert shipment.carrying_vessel is vessel
    assert vessel.carried_shipments == [shipment]
    if should_rebook:
        assert current not in route.associated_bookings
        assert shipment.get_current_booking().arrival_segment_index == 1
        assert shipment.associated_bookings[-1].service_route is alternative
        assert len(shipment.associated_bookings) == 3
    else:
        # Continuing costs 64 h. The old extra 48 h would incorrectly favor a 64 h transfer.
        assert shipment.associated_bookings == [prefix, current]
        assert alternative.associated_bookings == []
    port = origin
    for index, booking in enumerate(shipment.associated_bookings, 1):
        segments = {segment.sequence_index: segment for segment in booking.service_route.segments}
        assert booking.sequence_index == index
        assert segments[booking.departure_segment_index].associated_leg.departure_port is port
        port = segments[booking.arrival_segment_index].associated_leg.arrival_port
        assert booking in booking.service_route.associated_bookings
    assert port is destination
