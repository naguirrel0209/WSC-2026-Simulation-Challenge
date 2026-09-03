"""Risk-penalized expected-time booking strategy for Round 2 experiment 3."""

from dataclasses import dataclass
import datetime as dt
import math

from maritime_data_context import Booking


@dataclass
class _PathState:
    cost: float = math.inf
    transfers: int = 0
    previous_edge: object = None


class UserStrategy:
    """Minimize expected time with gradual penalties for upcoming disruptions."""

    FUTURE_LEG_HORIZON_DAYS = 45.0
    FUTURE_PORT_HORIZON_DAYS = 14.0
    FUTURE_LEG_RISK_FACTOR = 1.25
    FUTURE_PORT_RISK_FACTOR = 0.35
    TRANSFER_PENALTY_DAYS = 0.75
    MAX_HEADWAY_DAYS = 7.0

    @staticmethod
    def select_vessel_for_berth(
        maritime_data_context,
        port,
        waiting_vessels,
        available_berths,
        current_time,
        waiting_since_by_vessel=None,
    ):
        return None

    @staticmethod
    def create_alternative_service_routes(context, now, vessel=None):
        return None

    @staticmethod
    def assign_associated_bookings(context, now, shipment):
        # Import lazily because the simulation package and strategy package
        # initialize each other during test collection.
        from response_strategies.default_strategy import (
            _build_all_candidate_bookings,
            _remove_bookings_from_service_routes,
        )

        demand = shipment.demand
        origin_port = demand.origin_port
        destination_port = demand.destination_port

        _remove_bookings_from_service_routes(shipment.associated_bookings)
        shipment.associated_bookings = []
        shipment.current_booking_index = None

        if origin_port is destination_port:
            return True

        avoid_port_names, congested_legs = _get_active_disruption_filters(context, now)
        if destination_port.name.casefold() in avoid_port_names:
            return False

        edges = _build_all_candidate_bookings(
            context,
            avoid_port_names,
            congested_legs,
        )
        path = _find_expected_time_path(
            context,
            now,
            origin_port,
            destination_port,
            edges,
        )
        if not path:
            return False

        for sequence_index, edge in enumerate(path, start=1):
            booking = Booking(
                sequence_index=sequence_index,
                shipment=shipment,
                service_route=edge.service_route,
                departure_segment_index=edge.departure_segment_index,
                arrival_segment_index=edge.arrival_segment_index,
            )
            shipment.associated_bookings.append(booking)
            edge.service_route.associated_bookings.append(booking)

        shipment.current_booking_index = 1
        return True

    @staticmethod
    def adjust_bookings_before_cargo_handling(context, now, vessel):
        return None


def _find_expected_time_path(context, now, origin_port, destination_port, edges):
    outgoing = {}
    for edge in edges:
        outgoing.setdefault(edge.departure_port, []).append(edge)

    states = {port: _PathState() for port in context.ports}
    states[origin_port].cost = 0.0
    unvisited = list(context.ports)

    while unvisited:
        current = min(
            unvisited,
            key=lambda port: (states[port].cost, states[port].transfers),
        )
        if math.isinf(states[current].cost) or current is destination_port:
            break
        unvisited.remove(current)

        for edge in outgoing.get(current, []):
            next_port = edge.arrival_port
            if next_port not in unvisited:
                continue
            candidate_cost = (
                states[current].cost
                + _expected_edge_days(edge)
                + _future_edge_risk_days(context, now, edge, destination_port)
            )
            candidate_transfers = states[current].transfers + 1
            next_state = states[next_port]
            if (candidate_cost, candidate_transfers) >= (
                next_state.cost,
                next_state.transfers,
            ):
                continue
            next_state.cost = candidate_cost
            next_state.transfers = candidate_transfers
            next_state.previous_edge = edge

    if states[destination_port].previous_edge is None:
        return None

    path = []
    cursor = destination_port
    while cursor is not origin_port:
        edge = states[cursor].previous_edge
        if edge is None:
            return None
        path.append(edge)
        cursor = edge.departure_port
    path.reverse()
    return path


def _get_active_disruption_filters(context, now):
    avoid_port_names = set()
    congested_legs = set()
    for plan in context.disruption_plans:
        if not _is_active(plan, now):
            continue
        if plan.close_berth and plan.target_berth is not None:
            avoid_port_names.add(plan.target_berth.port.name.casefold())
        elif plan.multiplier > 1 and plan.target_leg is not None:
            congested_legs.add(plan.target_leg)
    return avoid_port_names, congested_legs


def _is_active(plan, now):
    if plan.start_offset_days is None or plan.duration_days is None:
        return False
    start = dt.datetime.min + dt.timedelta(days=plan.start_offset_days)
    end = start + dt.timedelta(days=plan.duration_days)
    return start <= now < end


def _future_edge_risk_days(context, now, edge, destination_port):
    segments = _edge_segments(edge)
    edge_legs = {segment.associated_leg for segment in segments}
    edge_arrival_ports = {
        segment.associated_leg.arrival_port for segment in segments
    }
    speed = _average_route_speed(edge.service_route)
    penalty = 0.0
    counted_port_plans = set()

    for plan in context.disruption_plans:
        if plan.multiplier > 1 and plan.target_leg in edge_legs:
            weight = _future_weight(
                plan,
                now,
                UserStrategy.FUTURE_LEG_HORIZON_DAYS,
            )
            if weight > 0:
                normal_days = plan.target_leg.sailing_distance / speed / 24.0
                penalty += (
                    normal_days
                    * (plan.multiplier - 1.0)
                    * weight
                    * UserStrategy.FUTURE_LEG_RISK_FACTOR
                )

        if not plan.close_berth or plan.target_berth is None:
            continue
        target_port = plan.target_berth.port
        if target_port is destination_port or target_port not in edge_arrival_ports:
            continue
        plan_key = (
            target_port.name.casefold(),
            plan.start_offset_days,
            plan.duration_days,
        )
        if plan_key in counted_port_plans:
            continue
        counted_port_plans.add(plan_key)
        weight = _future_weight(
            plan,
            now,
            UserStrategy.FUTURE_PORT_HORIZON_DAYS,
        )
        if weight > 0:
            penalty += (
                plan.duration_days
                * weight
                * UserStrategy.FUTURE_PORT_RISK_FACTOR
            )

    return penalty


def _future_weight(plan, now, horizon_days):
    if plan.start_offset_days is None or plan.duration_days is None:
        return 0.0
    start = dt.datetime.min + dt.timedelta(days=plan.start_offset_days)
    days_until_start = (start - now).total_seconds() / 86400.0
    if days_until_start <= 0 or days_until_start > horizon_days:
        return 0.0
    return 1.0 - days_until_start / horizon_days


def _edge_segments(edge):
    segments = sorted(
        edge.service_route.segments,
        key=lambda segment: segment.sequence_index,
    )
    index = edge.departure_segment_index - 1
    traversed = []
    for _ in range(len(segments)):
        segment = segments[index]
        traversed.append(segment)
        if segment.sequence_index == edge.arrival_segment_index:
            break
        index = (index + 1) % len(segments)
    return traversed


def _average_route_speed(route):
    speeds = [
        vessel.vessel_class.sailing_speed
        for vessel in route.deployed_vessels
        if vessel.vessel_class is not None
        and vessel.vessel_class.sailing_speed > 0
    ]
    return sum(speeds) / len(speeds) if speeds else 20.0


def _expected_edge_days(edge):
    route = edge.service_route
    vessels = list(route.deployed_vessels)
    speed = _average_route_speed(route)
    sailing_days = edge.total_distance / speed / 24.0
    cycle_distance = sum(
        segment.associated_leg.sailing_distance for segment in route.segments
    )
    cycle_days = cycle_distance / speed / 24.0
    headway_days = min(
        UserStrategy.MAX_HEADWAY_DAYS,
        cycle_days / max(1, len(vessels)),
    )
    expected_wait_days = headway_days / 2.0
    return (
        sailing_days
        + expected_wait_days
        + UserStrategy.TRANSFER_PENALTY_DAYS
    )
