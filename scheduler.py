"""Core scheduler."""
from typing import List, Dict
from models import Bus, ChargingPlan, ChargingAssignment, Scenario, Weights
from charging_planner import ChargingPlanner
from simulator import Simulator
from metrics_engine import MetricsEngine


class Scheduler:
    """Greedy scheduler with weighted objective optimization."""

    @staticmethod
    def schedule(buses: List[Bus], scenario: Scenario) -> List[ChargingAssignment]:
        """Generate charging assignments for all buses."""
        assignments = []
        station_queues: Dict[str, List] = {}

        # Sort buses by departure time for simulation order
        sorted_buses = sorted(buses, key=lambda b: b.departure_time)

        for bus in sorted_buses:
            # Generate charging plans for this bus
            plans = ChargingPlanner.plan(bus, scenario.route, scenario.stations)

            # For MVP, just take first valid plan
            if plans:
                plan = plans[0]
            else:
                plan = ChargingPlan(bus_id=bus.id, stations=[])

            # Simulate journey
            assignment = Simulator.simulate_journey(bus, plan, scenario, station_queues)

            # Update station queues with this bus's charging events
            for event in assignment.charging_events:
                if event.station_id not in station_queues:
                    station_queues[event.station_id] = []
                # Add end time to queue
                from datetime import datetime
                end_time = datetime.strptime(event.charging_end_time, "%H:%M")
                station_queues[event.station_id].append(end_time)

            assignments.append(assignment)

        return assignments
