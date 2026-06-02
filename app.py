"""Streamlit app for Bus Charging Scheduler."""
import streamlit as st
import json
from loader import ScenarioLoader
from validator import Validator
from scheduler import Scheduler
from metrics_engine import MetricsEngine
from output_formatter import OutputFormatter


def main():
    st.set_page_config(page_title="Bus Charging Scheduler", layout="wide")
    st.title("⚡ Bus Charging Scheduler")

    # Load scenarios
    with open('scenarios.json', 'r') as f:
        scenarios_data = json.load(f)

    scenarios = {}
    for key, scenario_data in scenarios_data.items():
        try:
            loader = ScenarioLoader()
            # Convert dict to Scenario object
            from models import Bus, Segment, Route, Station, Weights, Scenario

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

            scenarios[scenario_data['name']] = scenario
        except Exception as e:
            st.error(f"Failed to load {key}: {e}")

    # Scenario selector
    scenario_names = list(scenarios.keys())
    selected_scenario_name = st.selectbox("Select Scenario", scenario_names)
    scenario = scenarios[selected_scenario_name]

    # Display scenario input
    st.header("📋 Scenario Input")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Buses")
        bus_data = []
        for bus in scenario.buses:
            bus_data.append({
                'ID': bus.id,
                'Operator': bus.operator,
                'Direction': bus.direction,
                'Departure': bus.departure_time
            })
        st.dataframe(bus_data)

    with col2:
        st.subheader("Route & Stations")
        st.write("**Route Segments:**")
        seg_data = []
        for seg in scenario.route.segments:
            seg_data.append({
                'From': seg.from_point,
                'To': seg.to_point,
                'Distance': f"{seg.distance} km"
            })
        st.dataframe(seg_data)

        st.write("**Stations:**")
        sta_data = [{
            'Name': s.name,
            'Chargers': s.chargers
        } for s in scenario.stations]
        st.dataframe(sta_data)

    st.write("**Optimization Weights:**")
    weights_display = {
        'Individual': scenario.weights.individual,
        'Operator': scenario.weights.operator,
        'Overall': scenario.weights.overall
    }
    st.json(weights_display)

    # Compute schedule
    if st.button("🚀 Compute Schedule"):
        with st.spinner("Computing schedule..."):
            try:
                # Validate
                feasible, errors = Validator.validate(scenario)
                if not feasible:
                    st.error(f"Scenario not feasible:\n" + "\n".join(errors))
                    return

                # Schedule
                assignments = Scheduler.schedule(scenario.buses, scenario)

                # Compute metrics
                metrics = MetricsEngine.compute(assignments, scenario.weights)

                # Format output
                bus_timetables = OutputFormatter.format_bus_timetables(assignments, scenario)
                station_queues = OutputFormatter.format_station_queues(assignments, scenario)
                metrics_display = OutputFormatter.format_metrics(metrics)

                # Display results
                st.success("✅ Schedule computed successfully!")

                # Metrics summary
                st.header("📊 Performance Metrics")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Wait (min)", metrics_display['total_wait_time_minutes'])
                col2.metric("Operator Variance", metrics_display['operator_wait_variance'])
                col3.metric("Network Time (min)", metrics_display['network_completion_time_minutes'])
                col4.metric("Objective Score", metrics_display['weighted_objective'])

                # Per-bus timetables
                st.header("🚌 Per-Bus Timetables")
                for timetable in bus_timetables:
                    with st.expander(f"Bus {timetable['bus_id']} ({timetable['operator']})"):
                        st.write(f"**Departure:** {timetable['departure_time']}")
                        st.write(f"**Arrival:** {timetable['arrival_time']}")
                        st.write(f"**Total Wait:** {timetable['total_wait_time']} minutes")
                        st.write(f"**Charging Stations:** {', '.join(timetable['charging_stations']) if timetable['charging_stations'] else 'None'}")

                        if timetable['charging_events']:
                            st.write("**Charging Events:**")
                            event_data = []
                            for event in timetable['charging_events']:
                                event_data.append({
                                    'Station': event['station'],
                                    'Arrival': event['arrival'],
                                    'Wait (min)': event['wait_minutes'],
                                    'Start Charge': event['start_charging'],
                                    'End Charge': event['end_charging']
                                })
                            st.dataframe(event_data)

                # Per-station queues
                st.header("🔌 Per-Station Charging Queues")
                for station_id, queue in station_queues.items():
                    with st.expander(f"Station {station_id}"):
                        queue_data = []
                        for entry in queue:
                            queue_data.append({
                                'Bus': entry['bus_id'],
                                'Operator': entry['operator'],
                                'Start': entry['start_time'],
                                'End': entry['end_time'],
                                'Wait (min)': entry['wait_time']
                            })
                        st.dataframe(queue_data)

            except Exception as e:
                st.error(f"Error computing schedule: {e}")
                import traceback
                st.error(traceback.format_exc())


if __name__ == "__main__":
    main()
