"""Four-hook resilience policy. All quantities are hours and TEU.

rho is an occupancy proxy; half-headway is a slack proxy, not a timetable.
No loading-order or capacity-reservation interface exists in this simulator.
"""
import math
from collections import Counter
from maritime_data_context import Booking


def _default():
    from . import default_strategy
    return default_strategy


def _age(s, now):
    generated = getattr(s, "generated_time", None)
    return max(0, (now - generated).total_seconds() / 3600) if generated else 0


def _work(vessel, port):
    discharge = list(vessel.get_discharging_shipments_at_current_segment())
    next_segment = vessel.get_next_segment()
    occupied = sum(s.teu_size for s in vessel.carried_shipments if s not in discharge)
    capacity = max(0, vessel.vessel_class.teu_capacity - occupied)
    loaded = 0
    for s in port.shipments_in_storage:
        if s.carrying_vessel is not None:
            continue
        try:
            b = s.get_current_booking()
        except (ValueError, AttributeError):
            continue
        if (b.service_route is vessel.assigned_service_route
                and b.departure_segment_index == next_segment.sequence_index
                and loaded + s.teu_size <= capacity):
            loaded += s.teu_size
    productivity = max(1, round(vessel.vessel_class.loa / 50)) * 45.0
    return discharge, max((sum(s.teu_size for s in discharge) + loaded) / productivity, 1 / 60)


class _State:
    def __init__(self):
        self.queues = {}
        self.cache_key = None
        self.edges = []
        self.metrics = {}
        self.headways = {}
        self.paths = {}
        self.fleet_key = None
        self.errors = Counter()


class ResilienceStrategy:
    RHO_LIMIT = 0.80
    CONNECTION_BUFFER = 1.5
    FLEET_WAIT_HOURS = 84.0
    MIN_REBOOK_GAIN_HOURS = 12.0
    _context = None
    _state = None

    @classmethod
    def state(cls, context):
        if cls._context is not context:
            cls._context, cls._state = context, _State()
        return cls._state

    @classmethod
    def select_vessel_for_berth(cls, maritime_data_context, port, waiting_vessels,
                                available_berths, current_time, waiting_since_by_vessel=None):
        if not waiting_vessels:
            return None
        state = cls.state(maritime_data_context)
        try:
            work = {v: _work(v, port) for v in waiting_vessels}
            servers = max(1, sum(b.is_available for b in port.berths))
            state.queues[port] = (current_time, sum(3 + w[1] for w in work.values()) / servers)
            state.cache_key = None
            since = waiting_since_by_vessel or {}
            def score(v):
                cargo, hours = work[v]
                return (sum(_age(s, current_time) * s.teu_size for s in cargo) / hours,
                        (current_time - since.get(v, current_time)).total_seconds())
            return max(waiting_vessels, key=score)
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            state.errors["berth"] += 1
            return None

    @classmethod
    def _snapshot(cls, context, now):
        state = cls.state(context)
        key = (now.toordinal(), now.hour // 6,
               tuple((id(r), len(r.deployed_vessels)) for r in context.service_routes),
               tuple(b.is_available for p in context.ports for b in p.berths),
               tuple(l.sailing_time_multiplier for l in context.legs))
        if key == state.cache_key:
            return state
        metrics = {}
        for port in context.ports:
            opened = [b for b in port.berths if b.is_available]
            # berth.occupying_vessel may be stale; use vessel.current_berth.
            busy = [v for v in context.vessels if v.current_berth is not None and v.current_berth in opened]
            rho = len(busy) / len(opened) if opened else 1.0
            wait = 0.0 if opened else math.inf
            if opened and len(busy) >= len(opened):
                wait = sum(3 + _work(v, port)[1] for v in busy) / len(opened)
            observed = state.queues.get(port)
            if observed and (now - observed[0]).total_seconds() <= 6 * 3600:
                wait = max(wait, observed[1])
            metrics[port] = rho, wait
        d = _default()
        closed, congested = d._get_active_disruption_plans(context, now)
        avoid = d._get_avoid_port_names(closed)
        for p in context.ports:
            if not any(b.is_available for b in p.berths):
                avoid.add(p.name.casefold())
        edges = d._build_all_candidate_bookings(context, avoid, d._get_congested_legs(congested))
        headways = {}
        for route in context.service_routes:
            vessels = list(route.deployed_vessels)
            speeds = [v.vessel_class.sailing_speed for v in vessels if v.vessel_class.sailing_speed > 0]
            if not speeds:
                continue
            speed = sum(speeds) / len(speeds)
            cycle = sum(s.associated_leg.sailing_distance * s.associated_leg.sailing_time_multiplier / speed
                        + 3 for s in route.segments)
            headways[route] = speed, cycle / len(vessels)
        state.metrics, state.edges, state.headways = metrics, edges, headways
        state.paths, state.cache_key = {}, key
        return state

    @classmethod
    def _edge_cost(cls, state, edge, transfer):
        speed, headway = state.headways.get(edge.service_route, (0, math.inf))
        if speed <= 0:
            return math.inf
        rho, wait = state.metrics[edge.departure_port]
        slack = headway / 2
        if transfer and slack < cls.CONNECTION_BUFFER * wait:
            return math.inf
        penalty = 24 * max(0, (rho - cls.RHO_LIMIT) / (1 - cls.RHO_LIMIT)) if transfer else 0
        return edge.total_distance / speed + slack + wait + penalty + (18 if transfer else 0)

    @classmethod
    def _path(cls, state, origin, destination):
        key = origin, destination
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
                cost = costs[port] + cls._edge_cost(state, edge, port is not origin)
                if cost < costs.get(target, math.inf):
                    costs[target], paths[target] = cost, paths[port] + [edge]
                    pending.add(target)
        result = paths.get(destination), costs.get(destination, math.inf)
        state.paths[key] = result
        return result

    @classmethod
    def assign_associated_bookings(cls, context, now, shipment):
        state = cls.state(context)
        try:
            origin, destination = shipment.demand.origin_port, shipment.demand.destination_port
            if origin is destination:
                return None
            if not context.vessels or not origin.berths or not destination.berths:
                return None  # Incomplete API state: let the framework decide.
            path, _ = cls._path(cls._snapshot(context, now), origin, destination)
            if not path:
                return False
            bookings = [Booking(i, shipment, e.service_route, e.departure_segment_index, e.arrival_segment_index)
                        for i, e in enumerate(path, 1)]
            _commit(shipment, bookings, 1)
            return True
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            state.errors["booking"] += 1
            return None

    @classmethod
    def adjust_bookings_before_cargo_handling(cls, context, now, vessel):
        state = cls.state(context)
        try:
            segment = vessel.current_segment
            if segment is None:
                return True
            port = segment.associated_leg.arrival_port
            state = cls._snapshot(context, now)
            # Evaluate old cargo first, without modifying the engine's loading queue.
            for shipment in sorted(vessel.carried_shipments, key=lambda s: -_age(s, now)):
                current = shipment.get_current_booking()
                destination = shipment.demand.destination_port
                if destination is port:
                    continue
                path, new_cost = cls._path(state, port, destination)
                if not path:
                    continue
                old_cost = _remaining_cost(cls, state, shipment, current, segment)
                if path[0].service_route is not current.service_route:
                    if not math.isfinite(cls._edge_cost(state, path[0], True)):
                        continue
                    new_cost += 18
                if new_cost + max(cls.MIN_REBOOK_GAIN_HOURS, 0.1 * new_cost) >= old_cost:
                    continue
                prefix = [b for b in shipment.associated_bookings if b.sequence_index < current.sequence_index]
                completed = Booking(current.sequence_index, shipment, current.service_route,
                                    current.departure_segment_index, segment.sequence_index)
                tail = path
                if path[0].service_route is current.service_route:
                    completed.arrival_segment_index = path[0].arrival_segment_index
                    tail = path[1:]
                bookings = prefix + [completed] + [
                    Booking(current.sequence_index + i, shipment, e.service_route,
                            e.departure_segment_index, e.arrival_segment_index)
                    for i, e in enumerate(tail, 1)]
                _commit(shipment, bookings, current.sequence_index)
            return True
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            state.errors["rebooking"] += 1
            return None

    @classmethod
    def create_alternative_service_routes(cls, context, now, vessel=None):
        state = cls.state(context)
        try:
            d = _default()
            state = cls._snapshot(context, now)
            ports = ([vessel.get_next_segment().associated_leg.arrival_port]
                     if vessel is not None else list(context.ports))
            trigger = any(state.metrics[p][1] > cls.FLEET_WAIT_HOURS for p in ports)
            key = (now.toordinal(), now.hour // 6, d._get_active_disruption_key(context, now))
            candidates = [vessel] if vessel is not None else context.vessels
            needs_restore = any(v.pending_assigned_service_route is not None
                                or v.assigned_service_route.source_service_route is not None
                                for v in candidates)
            if not needs_restore and (not trigger or key == state.fleet_key):
                return True
            with _FleetTransaction(context):
                d._restore_inactive_alternative_route_vessels(context, now, vessel)
                if trigger and key != state.fleet_key:
                    d._ensure_alternative_service_routes(context, now)
                d._try_switch_empty_vessel_to_pending_route(vessel)
            if trigger:
                state.fleet_key = key
            return True
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            state.errors["fleet"] += 1
            return True  # rollback already restored assignments; safe no-op


def _remaining_cost(cls, state, shipment, current, segment):
    d, cost = _default(), 0.0
    for b in sorted(shipment.associated_bookings, key=lambda b: b.sequence_index):
        if b.sequence_index < current.sequence_index:
            continue
        segments = sorted(b.service_route.segments, key=lambda s: s.sequence_index)
        end = d._find_segment_list_index(segments, b.arrival_segment_index)
        if b is current:
            start = d._find_segment_list_index(segments, segment.sequence_index)
            if start < 0 or end < 0:
                return math.inf
            if start == end:
                continue
            start = (start + 1) % len(segments)
        else:
            start = d._find_segment_list_index(segments, b.departure_segment_index)
        if min(start, end) < 0:
            return math.inf
        legs = list(d._iter_segments_between(segments, start, end))
        if any(not math.isfinite(state.metrics[s.associated_leg.arrival_port][1])
               or s.associated_leg.sailing_time_multiplier > 1 for s in legs):
            return math.inf
        edge = d._CandidateBookingEdge(b.service_route, legs[0].associated_leg.departure_port,
                                     legs[-1].associated_leg.arrival_port, start + 1, end + 1,
                                     sum(s.associated_leg.sailing_distance for s in legs))
        cost += cls._edge_cost(state, edge, b is not current)
    return cost


def _commit(shipment, bookings, index):
    old, old_index = shipment.associated_bookings, shipment.current_booking_index
    if not old:
        # Initial bookings dominate hook calls. Avoid copying growing route
        # booking histories for each new shipment; keep an append undo log.
        appended = []
        try:
            for b in bookings:
                b.service_route.associated_bookings.append(b)
                appended.append(b)
            shipment.associated_bookings, shipment.current_booking_index = bookings, index
        except Exception:
            for b in reversed(appended):
                b.service_route.associated_bookings.remove(b)
            shipment.associated_bookings, shipment.current_booking_index = old, old_index
            raise
        return
    routes = {b.service_route for b in list(old) + bookings}
    saved = {r: list(r.associated_bookings) for r in routes}
    try:
        _default()._remove_bookings_from_service_routes(old)
        for b in bookings:
            b.service_route.associated_bookings.append(b)
        shipment.associated_bookings, shipment.current_booking_index = bookings, index
    except Exception:
        for r, values in saved.items():
            r.associated_bookings[:] = values
        shipment.associated_bookings, shipment.current_booking_index = old, old_index
        raise


class _FleetTransaction:
    """Rollback mutable strategy collections if construction/validation fails."""
    def __init__(self, context):
        self.context = context

    def __enter__(self):
        from .strategy_validation import capture_alternative_route_strategy_state
        c = self.context
        self.validation = capture_alternative_route_strategy_state(c)
        self.saved = []
        objects = [(c, ("service_routes", "partial_service_routes"))]
        objects += [(r, ("deployed_vessels",)) for r in c.service_routes]
        objects += [(l, ("segments",)) for l in c.legs]
        objects += [(s, ("current_vessels",)) for r in c.service_routes for s in r.segments]
        objects += [(v, ("assigned_service_route", "pending_assigned_service_route", "current_segment")) for v in c.vessels]
        for obj, fields in objects:
            for field in fields:
                value = getattr(obj, field)
                self.saved.append((obj, field, list(value) if isinstance(value, list) else value))
        return self

    def __exit__(self, kind, error, trace):
        try:
            if kind is None:
                from .strategy_validation import validate_alternative_route_strategy_result
                validate_alternative_route_strategy_result(self.context, self.validation)
                return False
        except Exception:
            self.restore()
            raise
        self.restore()
        return False

    def restore(self):
        for obj, field, value in self.saved:
            current = getattr(obj, field)
            if isinstance(current, list):
                current[:] = value
            else:
                setattr(obj, field, value)
