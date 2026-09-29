
from .round2_strategy import (
    assign_bookings,
    manage_service_routes,
    select_vessel_for_berth as select_round2_vessel_for_berth,
)


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
        return select_round2_vessel_for_berth(
            maritime_data_context,
            port,
            waiting_vessels,
            current_time,
            waiting_since_by_vessel,
        )

    @staticmethod
    def create_alternative_service_routes(context, now, vessel=None):
        return manage_service_routes(context, now, vessel)

    @staticmethod
    def assign_associated_bookings(context, now, shipment):
        return assign_bookings(context, now, shipment)

    @staticmethod
    def adjust_bookings_before_cargo_handling(context, now, vessel):
        return None
