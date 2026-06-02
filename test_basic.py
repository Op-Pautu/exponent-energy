"""Basic test to verify scheduler works."""
import json
from loader import ScenarioLoader
from validator import Validator
from scheduler import Scheduler
from metrics_engine import MetricsEngine
from output_formatter import OutputFormatter
from models import Bus, Segment, Route, Station, Weights, Scenario


def test_scenario_1():
    """Test Scenario 1."""
    print("Testing Scenario 1...")

    with open('scenarios.json', 'r') as f:
        scenarios_data = json.load(f)

    scenario_data = scenarios_data['scenario_1']

    # Build scenario
    buses = [Bus(**bus_data) for bus_data in scenario_data['buses']]

    route_data = scenario_data['route']
    segments = [Segment(
        from_point=seg['from'],
        to_point=seg['to'],
        distance=seg['distance'],
        order=seg['order']
    ) for seg in route_data['segments']]

    route = Route(
        name=route_data['name'],
        segments=sorted(segments, key=lambda s: s.order),
        endpoints=route_data['endpoints']
    )

    stations = [Station(
        id=sta['id'],
        name=sta['name'],
        location=sta.get('location', ''),
        chargers=sta.get('chargers', 1)
    ) for sta in scenario_data['stations']]

    weights_data = scenario_data.get('weights', {})
    weights = Weights(
        individual=float(weights_data.get('individual', 1.0)),
        operator=float(weights_data.get('operator', 1.0)),
        overall=float(weights_data.get('overall', 1.0))
    )

    scenario = Scenario(
        name=scenario_data['name'],
        buses=buses,
        route=route,
        stations=stations,
        weights=weights
    )

    # Validate
    feasible, errors = Validator.validate(scenario)
    if not feasible:
        print(f"❌ Validation failed: {errors}")
        return False
    print("✅ Validation passed")

    # Schedule
    try:
        assignments = Scheduler.schedule(scenario.buses, scenario)
        print(f"✅ Scheduler generated {len(assignments)} assignments")
    except Exception as e:
        print(f"❌ Scheduling failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Metrics
    try:
        metrics = MetricsEngine.compute(assignments, scenario.weights)
        print(f"✅ Metrics computed:")
        print(f"   - Total wait: {metrics.total_wait_time} min")
        print(f"   - Completion: {metrics.network_completion_time} min")
        print(f"   - Objective: {metrics.weighted_objective:.2f}")
    except Exception as e:
        print(f"❌ Metrics failed: {e}")
        return False

    # Output
    try:
        bus_timetables = OutputFormatter.format_bus_timetables(assignments, scenario)
        station_queues = OutputFormatter.format_station_queues(assignments, scenario)
        print(f"✅ Output formatted")
        print(f"   - {len(bus_timetables)} bus timetables")
        print(f"   - {len(station_queues)} station queues")
    except Exception as e:
        print(f"❌ Output failed: {e}")
        return False

    # Print sample timetable
    print(f"\n📋 Sample Bus Timetable:")
    for timetable in bus_timetables[:2]:
        print(f"  Bus {timetable['bus_id']}:")
        print(f"    Departure: {timetable['departure_time']}")
        print(f"    Arrival: {timetable['arrival_time']}")
        print(f"    Wait: {timetable['total_wait_time']} min")
        print(f"    Charges: {len(timetable['charging_events'])}")

    return True


if __name__ == "__main__":
    print("=" * 50)
    print("Bus Charging Scheduler - Basic Test")
    print("=" * 50)

    success = test_scenario_1()

    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed")
    print("=" * 50)
