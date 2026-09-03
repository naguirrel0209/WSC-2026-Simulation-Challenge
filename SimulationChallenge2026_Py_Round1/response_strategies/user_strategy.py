"""Conservative contestant strategy for the disruption scenario.

This file intentionally keeps the first competitive version close to the
validated fallback strategy. The previous implementation routed preventively
and replanned in transit with a broad lookahead, which lowered direct exposure
to disrupted arcs but created large transshipment backlogs. For KPI work, the
best baseline is a stable strategy that only intervenes where the simulator's
fallback already has explicit disruption handling.
"""

import datetime as dt

from maritime_data_context import Booking, Segment, ServiceRoute


_BOOKING_CACHE = {}
_S4_HOLDING_ROUTE_ID = "S4-KAOH-HOLDING"
_S4_HOLDING_ROUTE_KEY = (("s4-kaohsiung-holding-loop",), ())


class UserStrategy:
    @staticmethod
    def select_vessel_for_berth(
        maritime_data_context,
        port,
        waiting_vessels,
        available_berths,
        current_time,
        waiting_since_by_vessel=None,
    ):
        """Use the fallback berth rule."""
        return None

    @staticmethod
    def create_alternative_service_routes(context, now, vessel=None):
        """Hold S4 vessels in Asia instead of entering the 5x sailing legs."""
        _manage_s4_holding_route(context, now, vessel)
        return True

    @staticmethod
    def assign_associated_bookings(context, now, shipment):
        """Assign the fallback shortest path with reusable candidate caches."""
        return _assign_cached_fallback_booking(context, now, shipment)

    @staticmethod
    def adjust_bookings_before_cargo_handling(context, now, vessel):
        """Use the fallback in-transit rebooking strategy."""
        return None


def _assign_cached_fallback_booking(context, now, shipment):
    from response_strategies import default_strategy as fallback

    demand = shipment.demand
    origin_port = demand.origin_port
    destination_port = demand.destination_port

    _remove_bookings_from_service_routes(shipment.associated_bookings)
    shipment.associated_bookings = []
    shipment.current_booking_index = None

    if origin_port is destination_port:
        return True

    avoid_port_names = set()
    congested_legs = set()
    if _is_disruption_active(context, now):
        close_berth_plans, congested_leg_plans = fallback._get_active_disruption_plans(
            context, now
        )
        avoid_port_names = fallback._get_avoid_port_names(close_berth_plans)
        congested_legs = fallback._get_congested_legs(congested_leg_plans)

    if destination_port.name.casefold() in avoid_port_names:
        return False

    disruption_key = (
        tuple(sorted(avoid_port_names)),
        tuple(sorted(fallback._leg_key(leg) for leg in congested_legs)),
    )
    cache_key = (id(context), disruption_key)
    cached = _BOOKING_CACHE.get(cache_key)
    if cached is None:
        candidate_bookings = fallback._build_all_candidate_bookings(
            context, avoid_port_names, congested_legs
        )
        candidate_bookings.sort(key=_service_frequency_tiebreaker)
        cached = (
            candidate_bookings,
            {},
        )
        _BOOKING_CACHE[cache_key] = cached

    candidate_bookings, paths = cached
    path_key = (id(origin_port), id(destination_port))
    if path_key not in paths:
        paths[path_key] = fallback._find_shortest_booking_path(
            context,
            origin_port,
            destination_port,
            candidate_bookings,
        )

    path = paths[path_key]
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


def _remove_bookings_from_service_routes(bookings):
    for booking in bookings:
        service_route = booking.service_route
        if service_route is None:
            continue
        while booking in service_route.associated_bookings:
            service_route.associated_bookings.remove(booking)


def _service_frequency_tiebreaker(edge):
    """Prefer the most frequently served route when distance costs tie."""
    route = edge.service_route
    vessels = [
        vessel
        for vessel in route.deployed_vessels
        if vessel.assigned_service_route is route
        and vessel.vessel_class is not None
        and vessel.vessel_class.sailing_speed > 0
    ]
    if vessels:
        cycle_distance = sum(
            segment.associated_leg.sailing_distance for segment in route.segments
        )
        average_speed = sum(
            vessel.vessel_class.sailing_speed for vessel in vessels
        ) / len(vessels)
        estimated_headway = cycle_distance / average_speed / len(vessels)
    else:
        estimated_headway = float("inf")
    return (
        estimated_headway,
        route.id,
        edge.departure_segment_index,
        edge.arrival_segment_index,
    )


def _is_disruption_active(context, now):
    from response_strategies import default_strategy as fallback

    return any(fallback._is_active(plan, now) for plan in context.disruption_plans)


def _manage_s4_holding_route(context, now, vessel):
    source_route = next(
        (route for route in context.initial_service_routes if route.id == "S4"),
        None,
    )
    if source_route is None:
        return

    holding_route = next(
        (
            route
            for route in context.service_routes
            if route.id == _S4_HOLDING_ROUTE_ID
        ),
        None,
    )
    window = _kaohsiung_disruption_window(context)
    in_disruption_window = window is not None and window[0] <= now < window[1]

    if in_disruption_window:
        if holding_route is None:
            holding_route = _create_s4_holding_route(context, source_route)
        _switch_s4_vessel_to_holding_route(vessel, source_route, holding_route)
        return

    if (
        holding_route is not None
        and vessel is not None
        and vessel.assigned_service_route is holding_route
    ):
        _restore_s4_vessel_from_holding_route(
            vessel, source_route, holding_route
        )


def _kaohsiung_disruption_window(context):
    starts = []
    ends = []
    for plan in context.disruption_plans:
        if plan.start_offset_days is None or plan.duration_days is None:
            continue
        if not _plan_involves_kaohsiung(plan):
            continue
        start = dt.datetime.min + dt.timedelta(days=plan.start_offset_days)
        starts.append(start)
        ends.append(start + dt.timedelta(days=plan.duration_days))
    if not starts:
        return None
    return min(starts), max(ends)


def _plan_involves_kaohsiung(plan):
    if plan.target_berth is not None:
        return plan.target_berth.port.name.casefold() == "kaohsiung"
    if plan.target_leg is None:
        return False
    leg = plan.target_leg
    return (
        leg.departure_port.name.casefold() == "kaohsiung"
        or leg.arrival_port.name.casefold() == "kaohsiung"
    )


def _create_s4_holding_route(context, source_route):
    source_segments = {
        segment.sequence_index: segment
        for segment in source_route.segments
    }
    holding_route = ServiceRoute(
        id=_S4_HOLDING_ROUTE_ID,
        name="S4 Kaohsiung Holding Loop",
        start_day_of_week=source_route.start_day_of_week,
    )
    holding_route.source_service_route = source_route
    # Keep this route unavailable to cargo booking at every disruption state.
    holding_route.disruption_key = _S4_HOLDING_ROUTE_KEY

    for sequence_index, source_index in enumerate((1, 2, 6), start=1):
        leg = source_segments[source_index].associated_leg
        segment = Segment(sequence_index, leg, holding_route)
        holding_route.segments.append(segment)
        leg.segments.append(segment)
        context.partial_service_routes.append(segment)

    context.service_routes.append(holding_route)
    return holding_route


def _switch_s4_vessel_to_holding_route(vessel, source_route, holding_route):
    if (
        vessel is None
        or vessel.assigned_service_route is not source_route
        or vessel.current_berth is None
        or vessel.current_segment is None
        or vessel.current_segment.sequence_index != 2
    ):
        return False

    current_segment = vessel.current_segment
    current_port = current_segment.associated_leg.arrival_port
    reentry_segment = next(
        (
            segment
            for segment in holding_route.segments
            if segment.associated_leg.arrival_port is current_port
        ),
        None,
    )
    if reentry_segment is None:
        return False

    while vessel in current_segment.current_vessels:
        current_segment.current_vessels.remove(vessel)
    while vessel in source_route.deployed_vessels:
        source_route.deployed_vessels.remove(vessel)
    if vessel not in holding_route.deployed_vessels:
        holding_route.deployed_vessels.append(vessel)

    vessel.assigned_service_route = holding_route
    vessel.pending_assigned_service_route = None
    vessel.current_segment = reentry_segment
    if vessel not in reentry_segment.current_vessels:
        reentry_segment.current_vessels.append(vessel)
    return True


def _restore_s4_vessel_from_holding_route(
    vessel, source_route, holding_route
):
    current_segment = vessel.current_segment
    if current_segment is None or current_segment.associated_leg is None:
        return False
    current_port = current_segment.associated_leg.arrival_port
    reentry_segment = next(
        (
            segment
            for segment in sorted(
                source_route.segments,
                key=lambda candidate: candidate.sequence_index,
            )
            if segment.associated_leg.arrival_port is current_port
        ),
        None,
    )
    if reentry_segment is None:
        return False

    while vessel in current_segment.current_vessels:
        current_segment.current_vessels.remove(vessel)
    while vessel in holding_route.deployed_vessels:
        holding_route.deployed_vessels.remove(vessel)
    if vessel not in source_route.deployed_vessels:
        source_route.deployed_vessels.append(vessel)

    vessel.assigned_service_route = source_route
    vessel.pending_assigned_service_route = None
    vessel.current_segment = reentry_segment
    if vessel not in reentry_segment.current_vessels:
        reentry_segment.current_vessels.append(vessel)
    return True
