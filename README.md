# Bus Charging Scheduler

A Python + Streamlit application for scheduling electric bus charging across fixed routes with multiple charging stations. The scheduler optimizes charging station allocation based on three tunable objectives: individual bus wait times, operator fleet efficiency, and overall network throughput.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running Locally

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

### Using the App

1. Select a scenario from the dropdown
2. Review the scenario input (buses, route, stations, weights)
3. Click "Compute Schedule" to generate the charging plan
4. View:
   - Performance metrics (wait times, completion time, objective score)
   - Per-bus timetables (when each bus charges, how long it waits)
   - Per-station queues (order of buses at each charging station)

## How to Change Weights

Weights control the optimization priority. Edit `scenarios.json` and modify the `weights` field for any scenario:

```json
"weights": {
  "individual": 1.0,   // Priority for minimizing individual bus wait times
  "operator": 2.0,     // Priority for minimizing operator fleet wait variance (higher = favor operators)
  "overall": 1.0       // Priority for minimizing overall network completion time
}
```

Example:
- **Individual High** (10.0, 1.0, 1.0): Each bus charges as soon as possible, minimizing individual waits.
- **Operator High** (1.0, 10.0, 1.0): Buses from the same operator are prioritized, improving operator efficiency.
- **Overall High** (1.0, 1.0, 10.0): All buses complete their journeys as quickly as possible.

Run the scheduler after changing weights—new weights take effect immediately.

## How to Add a New Rule

The scheduler uses a modular architecture. Adding a new rule involves:

### Example: Add Priority Buses

1. **Update the Bus model** (`models.py`):
   ```python
   @dataclass
   class Bus:
       priority: int = 5  # 0-10, already included for this extension
   ```

2. **Modify the tie-breaking rule in scheduler** (`scheduler.py`):
   ```python
   # In the scheduler, when sorting buses for charging order:
   sorted_buses.sort(key=lambda b: (-b.priority, b.departure_time))  # Higher priority first
   ```

3. **Add priority to scenario data** (`scenarios.json`):
   ```json
   {
     "id": "bus-express-01",
     "operator": "kpn",
     "direction": "Bengaluru→Kochi",
     "departure_time": "19:00",
     "priority": 9  // High priority express bus
   }
   ```

### Example: Add Multiple Chargers per Station

1. **Update Station model** (`models.py`):
   ```python
   @dataclass
   class Station:
       chargers: int = 1  # Already included
   ```

2. **Modify queue logic in simulator** (`simulator.py`):
   ```python
   # Update _compute_wait_time to check available chargers:
   available = station.chargers - len(queue)
   if available > 0:
       return 0  # Charger available immediately
   ```

3. **Update scenario data** (`scenarios.json`):
   ```json
   {
     "id": "A",
     "name": "Station A",
     "chargers": 2  // Now has 2 chargers
   }
   ```

### Example: Add Time-of-Day Electricity Costs

1. **Extend Station metadata** (`scenarios.json`):
   ```json
   {
     "id": "A",
     "name": "Station A",
     "metadata": {
       "cost_per_minute": 0.5  // Cost in rupees per minute
     }
   }
   ```

2. **Update weighted objective** (`metrics_engine.py`):
   ```python
   # In compute(), add cost term:
   total_cost = sum(event.charging_duration * station.metadata['cost_per_minute'])
   metrics.weighted_objective += weights.cost * total_cost
   ```

## Data Structure Design

### Key Scenarios for Extensibility

The data model anticipates these future changes without code rewrites:

1. **Multiple Chargers per Station**: `Station.chargers` field already supports configurable counts.
2. **Priority Buses**: `Bus.priority` field enables priority-based scheduling.
3. **Driver Shift Constraints**: `Bus.metadata['driver_id']` and new `Driver` object can track shifts.
4. **Time-of-Day Costs**: `Station.metadata['cost_per_minute']` stores dynamic costs.
5. **Variable Charging Times**: `Station.charger_type` can map to different charging profiles.
6. **Multiple Routes**: `Route.name` and `Segment` objects support parameterized routes.
7. **New Operators**: `Bus.operator` string field allows unlimited operators.
8. **Battery Degradation**: `Bus.battery_range` is per-bus, not global.

### Architecture

- **Loader**: Parses scenario JSON into Python objects
- **Validator**: Checks feasibility (battery range, segment distances)
- **Charging Planner**: Enumerates valid charging plans via DFS
- **Scheduler**: Greedily assigns buses to plans and determines charging order
- **Simulator**: Simulates each bus's journey and computes wait times
- **Metrics Engine**: Computes performance scores (wait times, completion time, weighted objective)
- **Output Formatter**: Formats results for UI display

## Assumptions

- All buses travel at 60 km/h (constant speed)
- Charging always takes 25 minutes (fixed)
- All buses have 240 km battery range (configurable per bus)
- Route is linear (no backtracking)
- Chargers are always available (no failures)
- Optimization weights are non-negative
- Departure times are precise (no delays)

## Testing

Run the app with each scenario to verify:

1. **Scenario 1** (Even Spacing): Buses depart every 15 minutes. Baseline case, minimal contention.
2. **Scenario 2** (Bunched Start): Buses cluster at start. Tests heavy early contention.
3. **Scenario 3** (Asymmetric Load): Uneven traffic across directions. Tests load balancing.
4. **Scenario 4** (Operator Heavy): One operator dominates. Tests operator weighting.
5. **Scenario 5** (Worst Case): Maximum buses in minimal time window. Tests extreme contention.

All scenarios should produce feasible schedules with no constraint violations.

## Extensibility Pattern

To add a new feature:

1. **Check if data model supports it**: Most extensions can be added via scenario data (metadata, new fields).
2. **If not, extend the data model**: Add new fields or objects to `models.py` (backward compatible).
3. **Update the algorithm**: Modify `scheduler.py`, `simulator.py`, or create a new component.
4. **Update scenarios**: Add new data to `scenarios.json`.
5. **Test**: Run the app and verify no constraint violations.

This design ensures that feature additions rarely require core engine rewrites—they mostly require data changes and isolated algorithm updates.
