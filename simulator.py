"""Bus journey simulator."""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from models import Bus, Route, Station, ChargingPlan, ChargingEvent, ChargingAssignment, Scenario


class Simulator:
    """Simulates bus journeys and computes timelines."""
    TRAVEL_SPEED = 60  # km/h
    CHARGING_TIME = 25  # minutes

    @staticmethod
    def simulate_journey(bus: Bus, charging_plan: ChargingPlan,
                        scenario: Scenario, station_queues: Dict[str, List[float]]) -> ChargingAssignment:
        """Simulate a bus journey and return assignment with charging events."""

        # Parse departure time
        dep_time = datetime.strptime(bus.departure_time, "%H:%M")
        current_time = dep_time
        current_battery = 240
        charging_events = []

        # Get route points
        route_points = scenario.route.get_route_as_list()

        # Build segment distance map
        segment_map = {}
        for seg in scenario.route.segments:
            segment_map[(seg.from_point, seg.to_point)] = seg.distance
            segment_map[(seg.to_point, seg.from_point)] = seg.distance

        # Determine current position and travel direction
        if "Bengaluru" in bus.direction and "Kochi" in bus.direction:
            current_pos_idx = 0
        else:
            current_pos_idx = 0

        current_pos = route_points[current_pos_idx]
        total_wait_time = 0

        # Traverse route segments
        for seg in scenario.route.segments:
            from_point = seg.from_point
            to_point = seg.to_point
            distance = seg.distance

            # Check if we need to charge at a station in this direction
            if to_point in charging_plan.stations:
                # Find station object
                station_obj = None
                for st in scenario.stations:
                    if st.id == to_point or st.name == to_point:
                        station_obj = st
                        break

                if station_obj:
                    # Travel to station
                    travel_time_min = (distance / Simulator.TRAVEL_SPEED) * 60
                    current_time += timedelta(minutes=travel_time_min)
                    current_battery -= distance

                    # Compute wait time
                    wait_time = Simulator._compute_wait_time(station_obj.id, current_time, station_queues)
                    total_wait_time += wait_time

                    # Charge
                    charge_start = current_time + timedelta(minutes=wait_time)
                    charge_end = charge_start + timedelta(minutes=Simulator.CHARGING_TIME)

                    charging_events.append(ChargingEvent(
                        station_id=station_obj.id,
                        arrival_time=current_time.strftime("%H:%M"),
                        wait_time=wait_time,
                        charging_start_time=charge_start.strftime("%H:%M"),
                        charging_end_time=charge_end.strftime("%H:%M"),
                        battery_before=int(current_battery),
                        battery_after=240
                    ))

                    current_time = charge_end
                    current_battery = 240
            else:
                # Just travel
                travel_time_min = (distance / Simulator.TRAVEL_SPEED) * 60
                current_time += timedelta(minutes=travel_time_min)
                current_battery -= distance

        # Return assignment
        assignment = ChargingAssignment(
            bus_id=bus.id,
            operator=bus.operator,
            direction=bus.direction,
            departure_time=bus.departure_time,
            charging_plan=charging_plan,
            charging_events=charging_events,
            arrival_time=current_time.strftime("%H:%M"),
            total_wait_time=total_wait_time
        )

        return assignment

    @staticmethod
    def _compute_wait_time(station_id: str, arrival_time: datetime,
                           station_queues: Dict[str, List]) -> int:
        """Compute wait time at station based on queue."""
        if station_id not in station_queues:
            station_queues[station_id] = []

        queue = station_queues[station_id]
        if not queue:
            return 0  # No wait

        # Queue contains end datetime objects of previous charges
        latest_end_time = max(queue)
        if arrival_time >= latest_end_time:
            return 0  # We arrived after charger is free

        # We have to wait
        wait_diff = (latest_end_time - arrival_time).total_seconds() / 60
        return max(0, int(wait_diff))
