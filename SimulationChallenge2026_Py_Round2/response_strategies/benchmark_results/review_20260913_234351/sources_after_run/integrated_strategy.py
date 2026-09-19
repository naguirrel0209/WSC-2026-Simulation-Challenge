"""Candidate combining H1 with complete connections and slow-leg comparison.

Not the active entry point. See INTEGRATED_MECHANISMS.md for its H1 control.
"""
from dataclasses import dataclass
import math

from maritime_data_context import Booking
from . import default_strategy as default
from .h2_connection_strategy import H2ConnectionStrategy
from .resilience_strategy import _age, _commit


@dataclass
class TravelEdge(default._CandidateBookingEdge):
    weighted_distance: float


def _travel_edge(state, route, start, end):
    """Build a circular booking edge from zero-based positions, without edits."""
    segments = sorted(route.segments, key=lambda s: s.sequence_index)
    if not (0 <= start < len(segments) and 0 <= end < len(segments)):
        return None
    legs = [s.associated_leg for s in default._iter_segments_between(segments, start, end)]
    if any(a.arrival_port is not b.departure_port for a, b in zip(legs, legs[1:])):
        return None
    closed = getattr(state, 'closed_port_names', set())
    for leg in legs:
        for port in (leg.departure_port, leg.arrival_port):
            if (port.name.casefold() in closed
                    or not math.isfinite(state.metrics.get(port, (1, math.inf))[1])):
                return None
        if (not math.isfinite(leg.sailing_distance) or leg.sailing_distance < 0
                or not math.isfinite(leg.sailing_time_multiplier)
                or leg.sailing_time_multiplier <= 0):
            return None
    return TravelEdge(
        route, legs[0].departure_port, legs[-1].arrival_port,
        segments[start].sequence_index, segments[end].sequence_index,
        sum(leg.sailing_distance for leg in legs),
        sum(leg.sailing_distance * leg.sailing_time_multiplier for leg in legs),
    )


def _candidate_edges(context, state, disruption_key):
    edges = []
    for route in context.service_routes:
        if (route not in state.headways
                or not default._route_is_available_for_booking(route, disruption_key)):
            continue
        size = len(route.segments)
        for start in range(size):
            # Preserve the control's maximum booking length: less than one cycle.
            for count in range(1, size):
                edge = _travel_edge(state, route, start, (start + count - 1) % size)
                if edge is not None and edge.departure_port is not edge.arrival_port:
                    edges.append(edge)
    return edges


class IntegratedStrategy(H2ConnectionStrategy):
    _context = None
    _state = None

    @classmethod
    def _snapshot(cls, context, now):
        state = cls.state(context)
        disruption_key = default._get_active_disruption_key(context, now)
        if getattr(state, 'booking_disruption_key', None) != disruption_key:
            state.cache_key = None
        old_edges = state.edges
        # Reuse the unchanged berth metrics and fleet/headway estimator. The
        # parent invalidates its graph when availability/multipliers change.
        state = super()._snapshot(context, now)
        if state.edges is not old_edges:
            closed, _ = default._get_active_disruption_plans(context, now)
            state.closed_port_names = set(default._get_avoid_port_names(closed))
            state.closed_port_names.update(p.name.casefold() for p, (_, wait)
                                           in state.metrics.items() if not math.isfinite(wait))
            state.edges = _candidate_edges(context, state, disruption_key)
            state.paths = {}
            state.booking_disruption_key = disruption_key
        return state

    @classmethod
    def _edge_cost(cls, state, edge, transfer, *, onboard=False):
        speed, headway = state.headways.get(edge.service_route, (0, math.inf))
        rho, wait = state.metrics.get(edge.departure_port, (1, math.inf))
        closed = getattr(state, 'closed_port_names', set())
        if (speed <= 0 or not all(map(math.isfinite, (speed, headway, wait, edge.weighted_distance)))
                or not math.isfinite(state.metrics.get(edge.arrival_port, (1, math.inf))[1])
                or edge.departure_port.name.casefold() in closed
                or edge.arrival_port.name.casefold() in closed):
            return math.inf
        slack = headway / 2
        cost = edge.weighted_distance / speed + (0 if onboard else slack) + wait
        if transfer:
            cost += (18 + 24 * max(0, (rho - cls.RHO_LIMIT) / (1 - cls.RHO_LIMIT))
                     + max(0, cls.CONNECTION_BUFFER * wait - slack))
        return cost

    @classmethod
    def _path(cls, state, origin, destination, *, continuation=None):
        key = origin, destination, continuation
        if key in state.paths:
            return state.paths[key]
        costs, paths, pending, visited = {origin: 0}, {origin: []}, {origin}, set()
        outgoing = {}
        for edge in state.edges:
            outgoing.setdefault(edge.departure_port, []).append(edge)
        while pending:
            port = min(pending, key=lambda p: (costs[p], p.name))
            pending.remove(port)
            if port is destination:
                break
            visited.add(port)
            for edge in outgoing.get(port, []):
                target = edge.arrival_port
                if target in visited:
                    continue
                onboard = port is origin and cls._continues(edge, continuation)
                transfer = port is not origin or (continuation is not None and not onboard)
                cost = costs[port] + cls._edge_cost(state, edge, transfer, onboard=onboard)
                if cost < costs.get(target, math.inf):
                    costs[target], paths[target] = cost, paths[port] + [edge]
                    pending.add(target)
        result = paths.get(destination), costs.get(destination, math.inf)
        state.paths[key] = result
        return result

    @classmethod
    def _remaining_cost(cls, state, shipment, current, segment):
        cost = 0.0
        for booking in sorted(shipment.associated_bookings, key=lambda b: b.sequence_index):
            if booking.sequence_index < current.sequence_index:
                continue
            segments = sorted(booking.service_route.segments, key=lambda s: s.sequence_index)
            end = default._find_segment_list_index(segments, booking.arrival_segment_index)
            if booking is current:
                start = default._find_segment_list_index(segments, segment.sequence_index)
                if min(start, end) < 0:
                    return math.inf
                if start == end:
                    continue
                start = (start + 1) % len(segments)
            else:
                start = default._find_segment_list_index(segments, booking.departure_segment_index)
            edge = _travel_edge(state, booking.service_route, start, end)
            if edge is None:
                return math.inf
            cost += cls._edge_cost(state, edge, booking is not current, onboard=booking is current)
        return cost

    @classmethod
    def adjust_bookings_before_cargo_handling(cls, context, now, vessel):
        state = cls.state(context)
        try:
            segment = vessel.current_segment
            if segment is None:
                return True
            port = segment.associated_leg.arrival_port
            state = cls._snapshot(context, now)
            continuation = vessel.assigned_service_route, vessel.get_next_segment().sequence_index
            for shipment in sorted(vessel.carried_shipments, key=lambda s: -_age(s, now)):
                current = shipment.get_current_booking()
                destination = shipment.demand.destination_port
                if destination is port:
                    continue
                path, new_cost = cls._path(state, port, destination, continuation=continuation)
                if not path:
                    continue
                old_cost = cls._remaining_cost(state, shipment, current, segment)
                if new_cost + max(cls.MIN_REBOOK_GAIN_HOURS, 0.1 * new_cost) >= old_cost:
                    continue
                prefix = [b for b in shipment.associated_bookings if b.sequence_index < current.sequence_index]
                completed = Booking(current.sequence_index, shipment, current.service_route,
                                    current.departure_segment_index, segment.sequence_index)
                tail = path
                if cls._continues(path[0], continuation):
                    completed.arrival_segment_index = path[0].arrival_segment_index
                    tail = path[1:]
                bookings = prefix + [completed] + [
                    Booking(current.sequence_index + i, shipment, e.service_route,
                            e.departure_segment_index, e.arrival_segment_index)
                    for i, e in enumerate(tail, 1)]
                _commit(shipment, bookings, current.sequence_index)
            return True
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            state.errors['rebooking'] += 1
            return None
