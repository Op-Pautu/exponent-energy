"""Feasibility validator."""
from models import Scenario, Bus
from typing import List, Tuple


class Validator:
    """Validates scenario feasibility."""
    BATTERY_RANGE = 240

    @staticmethod
    def validate(scenario: Scenario) -> Tuple[bool, List[str]]:
        """Check if scenario is feasible. Returns (feasible, errors)."""
        errors = []

        for bus in scenario.buses:
            # Get bus direction and segments
            direction = bus.direction
            if "→" in direction:
                parts = direction.split("→")
                start, end = parts[0].strip(), parts[1].strip()
            else:
                start, end = "Bengaluru", "Kochi"

            # Check if bus can traverse the route
            segments = sorted(scenario.route.segments, key=lambda s: s.order)

            # For direction, determine which way we're going
            if "Bengaluru" in start and "Kochi" in end:
                # Going forward, use segments as-is
                pass
            elif "Kochi" in start and "Bengaluru" in end:
                # Going backward, reverse segments
                segments = segments[::-1]

            # Find longest segment
            if segments:
                longest = max(s.distance for s in segments)
                if longest > Validator.BATTERY_RANGE:
                    errors.append(f"Bus {bus.id}: Segment {longest} km exceeds battery range {Validator.BATTERY_RANGE} km")

            # Check if route is completable with available stations
            # Get station count
            num_stations = len(scenario.stations)
            total_distance = sum(s.distance for s in segments)

            if total_distance > 0 and not Validator._can_complete_route(total_distance, num_stations, Validator.BATTERY_RANGE):
                errors.append(f"Bus {bus.id}: Cannot complete route (total {total_distance} km, battery {Validator.BATTERY_RANGE} km)")

        return len(errors) == 0, errors

    @staticmethod
    def _can_complete_route(total_distance: int, num_stations: int, battery_range: int) -> bool:
        """Check if route can be completed with available stations."""
        # Simple heuristic: if total distance is reachable with available stations
        # Maximum distance we can cover: battery_range * (1 + num_stations)
        max_possible = battery_range * (1 + num_stations)
        return total_distance <= max_possible
