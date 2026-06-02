"""Metrics computation engine."""
from typing import List, Dict
from models import ChargingAssignment, Metrics, Weights
import statistics


class MetricsEngine:
    """Computes performance metrics."""

    @staticmethod
    def compute(assignments: List[ChargingAssignment], weights: Weights) -> Metrics:
        """Compute metrics for all assignments."""
        metrics = Metrics()

        # Total wait time
        total_wait = sum(a.total_wait_time for a in assignments)
        metrics.total_wait_time = total_wait

        # Operator wait times
        operator_waits = {}
        for assignment in assignments:
            op = assignment.operator
            if op not in operator_waits:
                operator_waits[op] = 0
            operator_waits[op] += assignment.total_wait_time

        metrics.operator_wait_times = operator_waits

        # Operator wait variance
        if operator_waits:
            waits = list(operator_waits.values())
            if len(waits) > 1:
                metrics.operator_wait_variance = statistics.variance(waits)
            else:
                metrics.operator_wait_variance = 0.0

        # Network completion time
        if assignments:
            from datetime import datetime
            times = []
            for a in assignments:
                try:
                    t = datetime.strptime(a.arrival_time, "%H:%M")
                    times.append(t)
                except:
                    pass

            if times:
                latest = max(times)
                earliest = datetime.strptime(assignments[0].departure_time, "%H:%M")
                diff = (latest - earliest).total_seconds() / 60
                metrics.network_completion_time = int(diff)

        # Weighted objective
        metrics.weighted_objective = (
            weights.individual * metrics.total_wait_time +
            weights.operator * metrics.operator_wait_variance +
            weights.overall * metrics.network_completion_time
        )

        # Per-bus metrics
        for a in assignments:
            metrics.per_bus_metrics[a.bus_id] = {
                'wait_time': a.total_wait_time,
                'arrival_time': a.arrival_time,
                'num_charges': len(a.charging_events)
            }

        return metrics
