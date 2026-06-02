"""Charging plan generator using DFS."""
from models import Bus, Route, Station, ChargingPlan
from typing import List, Dict


class ChargingPlanner:
    """Generates valid charging plans for buses."""
    BATTERY_RANGE = 240

    @staticmethod
    def plan(bus: Bus, route: Route, stations: List[Station]) -> List[ChargingPlan]:
        """Generate all valid charging plans for a bus using DFS."""
        plans = []
        route_points = route.get_route_as_list()

        # Build segment map for distance lookup
        segment_map = {}
        for seg in route.segments:
            segment_map[(seg.from_point, seg.to_point)] = seg.distance

        # DFS to find all valid plans
        def dfs(current_idx: int, battery: int, stations_used: List[str], current_location: str):
            # If we reached the end
            if current_idx >= len(route_points) - 1:
                plans.append(ChargingPlan(
                    bus_id=bus.id,
                    stations=stations_used,
                    is_mandatory=False
                ))
                return

            next_point = route_points[current_idx + 1]
            distance = segment_map.get((current_location, next_point), 0)

            # Option 1: Travel to next point without charging
            if distance <= battery:
                dfs(current_idx + 1, battery - distance, stations_used, next_point)

            # Option 2: Charge at a station before traveling
            for station in stations:
                station_idx = -1
                try:
                    station_idx = route_points.index(station.id)
                except ValueError:
                    try:
                        station_idx = route_points.index(station.name)
                    except ValueError:
                        pass

                # If station is ahead and reachable
                if station_idx > current_idx and station_idx <= len(route_points) - 1:
                    dist_to_station = segment_map.get((current_location, station.id if station.id in route_points else station.name), 0)
                    if not dist_to_station:
                        dist_to_station = segment_map.get((current_location, station.name), 0)

                    if dist_to_station > 0 and dist_to_station <= battery:
                        # Charge at this station
                        new_stations = stations_used + [station.id]
                        dfs(station_idx - 1, 240, new_stations, station.id if station.id in route_points else station.name)

        # Start DFS from first point with full battery
        start_point = route_points[0]
        dfs(0, ChargingPlanner.BATTERY_RANGE, [], start_point)

        # If only one plan, mark as mandatory
        if len(plans) == 1:
            plans[0].is_mandatory = True

        return plans if plans else [ChargingPlan(bus_id=bus.id, stations=[])]
