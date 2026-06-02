"""Scenario loader."""
import json
from pathlib import Path
from models import Bus, Segment, Route, Station, Weights, Scenario


class ScenarioLoader:
    """Loads and parses scenario JSON files."""

    @staticmethod
    def load(filepath: str) -> Scenario:
        """Load scenario from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Validate required top-level fields
        required_fields = ['name', 'buses', 'route', 'stations', 'weights']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Parse buses
        buses = []
        for bus_data in data['buses']:
            required_bus_fields = ['id', 'operator', 'direction', 'departure_time']
            for field in required_bus_fields:
                if field not in bus_data:
                    raise ValueError(f"Bus missing required field: {field}")

            buses.append(Bus(
                id=bus_data['id'],
                operator=bus_data['operator'],
                direction=bus_data['direction'],
                departure_time=bus_data['departure_time'],
                battery_range=bus_data.get('battery_range', 240),
                priority=bus_data.get('priority', 5),
                metadata=bus_data.get('metadata', {})
            ))

        # Parse route
        route_data = data['route']
        segments = []
        for seg_data in route_data['segments']:
            segments.append(Segment(
                from_point=seg_data['from'],
                to_point=seg_data['to'],
                distance=int(seg_data['distance']),
                order=int(seg_data.get('order', len(segments)))
            ))

        route = Route(
            name=route_data.get('name', 'Route'),
            segments=sorted(segments, key=lambda s: s.order),
            endpoints=route_data['endpoints']
        )

        # Parse stations
        stations = []
        for sta_data in data['stations']:
            stations.append(Station(
                id=sta_data['id'],
                name=sta_data['name'],
                location=sta_data.get('location', ''),
                chargers=int(sta_data.get('chargers', 1)),
                charger_type=sta_data.get('charger_type', 'standard'),
                metadata=sta_data.get('metadata', {})
            ))

        # Parse weights
        weights_data = data.get('weights', {})
        weights = Weights(
            individual=float(weights_data.get('individual', 1.0)),
            operator=float(weights_data.get('operator', 1.0)),
            overall=float(weights_data.get('overall', 1.0))
        )

        return Scenario(
            name=data['name'],
            buses=buses,
            route=route,
            stations=stations,
            weights=weights,
            metadata=data.get('metadata', {})
        )

    @staticmethod
    def load_all_scenarios(scenarios_dir: str) -> dict:
        """Load all scenarios from directory."""
        scenarios = {}
        for filepath in Path(scenarios_dir).glob('*.json'):
            try:
                scenario = ScenarioLoader.load(str(filepath))
                scenarios[scenario.name] = scenario
            except Exception as e:
                print(f"Failed to load {filepath}: {e}")
        return scenarios
