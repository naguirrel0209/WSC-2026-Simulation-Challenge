"""Isolated H2 candidate. See H2_HYPOTHESIS.md; never imported by user_strategy.

Base is a byte-exact copy of the pre-H1 control. H1 and H3 are disabled.
"""
import math

from maritime_data_context import Booking
from .h2_control_strategy import ResilienceStrategy, _age, _commit, _remaining_cost


class H2ConnectionStrategy(ResilienceStrategy):
    _context = None
    _state = None

    @classmethod
    def _edge_cost(cls, state, edge, transfer):
        speed, headway = state.headways.get(edge.service_route, (0, math.inf))
        rho, wait = state.metrics[edge.departure_port]
        if (speed <= 0 or not all(map(math.isfinite, (speed, headway, wait)))
                or not math.isfinite(state.metrics[edge.arrival_port][1])):
            return math.inf
        slack = headway / 2
        cost = edge.total_distance / speed + slack + wait  # H1 deliberately absent.
        if transfer:
            occupancy = 24 * max(0, (rho - cls.RHO_LIMIT) / (1 - cls.RHO_LIMIT))
            missing_slack = max(0, cls.CONNECTION_BUFFER * wait - slack)
            cost += 18 + occupancy + missing_slack
        return cost

    @staticmethod
    def _continues(edge, continuation):
        return (continuation is not None and edge.service_route is continuation[0]
                and edge.departure_segment_index == continuation[1])

    @classmethod
    def _path(cls, state, origin, destination, *, continuation=None):
        # Origin bookings and arrivals with cargo have different first-edge
        # costs, even at the same port. The next index distinguishes repeat calls
        # to a port on circular routes (e.g. the two Piraeus calls on S1).
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
                transfer = (port is not origin or
                            (continuation is not None and not cls._continues(edge, continuation)))
                cost = costs[port] + cls._edge_cost(state, edge, transfer)
                if cost < costs.get(target, math.inf):
                    costs[target], paths[target] = cost, paths[port] + [edge]
                    pending.add(target)
        result = paths.get(destination), costs.get(destination, math.inf)
        state.paths[key] = result
        return result

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
                old_cost = _remaining_cost(cls, state, shipment, current, segment)
                # All transfer costs are already included by the path search.
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
