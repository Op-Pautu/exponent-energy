"""Data models for Bus Charging Scheduler."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


@dataclass
class Bus:
    """Represents an electric bus."""
    id: str
    operator: str
    direction: str  # "BNG→KCH" or "KCH→BNG"
    departure_time: str  # HH:MM format
    battery_range: int = 240  # km
    priority: int = 5  # 0-10, default 5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"Bus({self.id}, {self.operator}, {self.direction}, depart={self.departure_time})"


@dataclass
class Segment:
    """Represents a route segment."""
    from_point: str
    to_point: str
    distance: int  # km
    order: int  # Position in route


@dataclass
class Route:
    """Represents the entire route."""
    name: str
    segments: List[Segment]
    endpoints: Dict[str, str]  # {"start": "Bengaluru", "end": "Kochi"}

    def get_route_as_list(self) -> List[str]:
        """Return ordered list of all points in route."""
        points = [self.endpoints["start"]]
        for seg in sorted(self.segments, key=lambda s: s.order):
            points.append(seg.to_point)
        return points


@dataclass
class Station:
    """Represents a charging station."""
    id: str
    name: str
    location: str
    chargers: int = 1
    charger_type: str = "standard"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"Station({self.name}, chargers={self.chargers})"


@dataclass
class Weights:
    """Optimization weights."""
    individual: float = 1.0
    operator: float = 1.0
    overall: float = 1.0


@dataclass
class Scenario:
    """Complete scenario specification."""
    name: str
    buses: List[Bus]
    route: Route
    stations: List[Station]
    weights: Weights
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChargingPlan:
    """A charging plan for a bus."""
    bus_id: str
    stations: List[str]  # Station IDs in order
    is_mandatory: bool = False
    feasibility_reason: str = ""

    def __repr__(self):
        return f"ChargingPlan({self.bus_id}, {self.stations})"


@dataclass
class ChargingEvent:
    """A single charging event."""
    station_id: str
    arrival_time: str  # HH:MM format
    wait_time: int  # minutes
    charging_start_time: str
    charging_end_time: str
    battery_before: int  # km range
    battery_after: int = 240  # always 240 after charging


@dataclass
class ChargingAssignment:
    """Assignment of a bus to a charging plan with actual events."""
    bus_id: str
    operator: str
    direction: str
    departure_time: str
    charging_plan: ChargingPlan
    charging_events: List[ChargingEvent] = field(default_factory=list)
    arrival_time: str = ""
    total_wait_time: int = 0


@dataclass
class StationQueue:
    """Queue of buses at a station."""
    station_id: str
    queue: List[Dict[str, Any]] = field(default_factory=list)  # {bus_id, start_time, end_time}


@dataclass
class Metrics:
    """Performance metrics for a schedule."""
    total_wait_time: int = 0  # minutes
    operator_wait_times: Dict[str, int] = field(default_factory=dict)
    operator_wait_variance: float = 0.0
    network_completion_time: int = 0  # minutes
    weighted_objective: float = 0.0
    per_bus_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class Schedule:
    """Complete schedule output."""
    scenario_name: str
    charging_assignments: List[ChargingAssignment] = field(default_factory=list)
    station_queues: List[StationQueue] = field(default_factory=list)
    metrics: Metrics = field(default_factory=Metrics)
    feasible: bool = False
    validation_report: str = ""
