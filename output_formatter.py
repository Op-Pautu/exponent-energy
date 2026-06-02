"""Output formatting for display."""
from typing import List, Dict, Any
from models import ChargingAssignment, StationQueue, Scenario, Metrics
import json


class OutputFormatter:
    """Formats schedule output for display."""

    @staticmethod
    def format_bus_timetables(assignments: List[ChargingAssignment], scenario: Scenario) -> List[Dict[str, Any]]:
        """Format per-bus timetables."""
        timetables = []

        for assignment in assignments:
            timetable = {
                'bus_id': assignment.bus_id,
                'operator': assignment.operator,
                'direction': assignment.direction,
                'departure_time': assignment.departure_time,
                'arrival_time': assignment.arrival_time,
                'total_wait_time': assignment.total_wait_time,
                'charging_stations': assignment.charging_plan.stations,
                'charging_events': [
                    {
                        'station': event.station_id,
                        'arrival': event.arrival_time,
                        'wait_minutes': event.wait_time,
                        'start_charging': event.charging_start_time,
                        'end_charging': event.charging_end_time,
                        'battery_before': event.battery_before
                    }
                    for event in assignment.charging_events
                ]
            }
            timetables.append(timetable)

        return timetables

    @staticmethod
    def format_station_queues(assignments: List[ChargingAssignment], scenario: Scenario) -> Dict[str, Any]:
        """Format per-station charging queues."""
        queues_by_station = {}

        for assignment in assignments:
            for event in assignment.charging_events:
                station_id = event.station_id
                if station_id not in queues_by_station:
                    queues_by_station[station_id] = []

                queues_by_station[station_id].append({
                    'bus_id': assignment.bus_id,
                    'operator': assignment.operator,
                    'start_time': event.charging_start_time,
                    'end_time': event.charging_end_time,
                    'wait_time': event.wait_time
                })

        # Sort by start time
        for station_id in queues_by_station:
            queues_by_station[station_id].sort(key=lambda x: x['start_time'])

        return queues_by_station

    @staticmethod
    def format_metrics(metrics: Metrics) -> Dict[str, Any]:
        """Format metrics for display."""
        return {
            'total_wait_time_minutes': metrics.total_wait_time,
            'operator_wait_times': metrics.operator_wait_times,
            'operator_wait_variance': round(metrics.operator_wait_variance, 2),
            'network_completion_time_minutes': metrics.network_completion_time,
            'weighted_objective': round(metrics.weighted_objective, 2),
            'per_bus_summary': metrics.per_bus_metrics
        }
