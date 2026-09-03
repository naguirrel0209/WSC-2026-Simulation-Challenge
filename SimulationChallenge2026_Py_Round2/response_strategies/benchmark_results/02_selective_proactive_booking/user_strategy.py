"""Selective proactive booking strategy for Round 2 experiment 2."""

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
    """Minimize expected time and anticipate only new booking assignments."""

    CONGESTED_LEG_LOOKAHEAD_DAYS = 35.0
    CLOSED_PORT_LOOKAHEAD_DAYS = 7.0
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

        avoid_port_names, congested_legs = _get_planned_disruption_filters(
            context,
            now,
            destination_port,
        )
        if destination_port.name.casefold() in avoid_port_names:
            return False

        edges = _build_all_candidate_bookings(
            context,
            avoid_port_names,
            congested_legs,
        )
        path = _find_expected_time_path(
            context,
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


def _find_expected_time_path(context, origin_port, destination_port, edges):
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
            candidate_cost = states[current].cost + _expected_edge_days(edge)
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


def _get_planned_disruption_filters(context, now, destination_port):
    active_plans = [plan for plan in context.disruption_plans if _is_active(plan, now)]
    if active_plans:
        relevant_plans = active_plans
    else:
        relevant_plans = [
            plan
            for plan in context.disruption_plans
            if _starts_within_type_horizon(plan, now)
        ]

    avoid_port_names = set()
    congested_legs = set()
    for plan in relevant_plans:
        if plan.close_berth and plan.target_berth is not None:
            target_port = plan.target_berth.port
            if _is_active(plan, now) or target_port is not destination_port:
                avoid_port_names.add(target_port.name.casefold())
        elif plan.multiplier > 1 and plan.target_leg is not None:
            congested_legs.add(plan.target_leg)
    return avoid_port_names, congested_legs


def _is_active(plan, now):
    if plan.start_offset_days is None or plan.duration_days is None:
        return False
    start = dt.datetime.min + dt.timedelta(days=plan.start_offset_days)
    end = start + dt.timedelta(days=plan.duration_days)
    return start <= now < end


def _starts_within_type_horizon(plan, now):
    if plan.start_offset_days is None or plan.duration_days is None:
        return False
    start = dt.datetime.min + dt.timedelta(days=plan.start_offset_days)
    end = start + dt.timedelta(days=plan.duration_days)
    lookahead_days = (
        UserStrategy.CLOSED_PORT_LOOKAHEAD_DAYS
        if plan.close_berth
        else UserStrategy.CONGESTED_LEG_LOOKAHEAD_DAYS
    )
    horizon = now + dt.timedelta(days=lookahead_days)
    return now < start <= horizon and end > now


def _expected_edge_days(edge):
    route = edge.service_route
    vessels = list(route.deployed_vessels)
    speeds = [
        vessel.vessel_class.sailing_speed
        for vessel in vessels
        if vessel.vessel_class is not None
        and vessel.vessel_class.sailing_speed > 0
    ]
    if not speeds:
        speeds = [20.0]

    speed = sum(speeds) / len(speeds)
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
