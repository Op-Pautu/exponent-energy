# Bus Charging Scheduler - Architecture Documentation

## Overview

The Bus Charging Scheduler is a Python + Streamlit application that optimizes the allocation of limited charging resources across electric buses traveling fixed routes. The system uses a **greedy algorithm with weighted objective optimization** to balance three competing goals: minimizing individual bus wait times, maintaining operator fleet efficiency, and reducing overall network completion time.

## Core Design Principles

1. **Constraint-First**: Physical constraints (240 km battery range, single charger per station, 25-minute charging time) are enforced first; optimization happens within feasible space.

2. **Data-Driven Configuration**: Weights, charger counts, bus priorities, and rules are stored in scenario JSON files, not hardcoded in code.

3. **Modular Architecture**: Each component has a single responsibility and clear interfaces. Components are independent and can be tested/extended separately.

4. **Simulation-Based Validation**: All schedules are validated through event-based simulation before display.

5. **Extensibility by Design**: The data model and architecture anticipate future changes (priority buses, multiple chargers, time-of-day costs, driver shifts) without requiring core algorithm rewrites.

## System Architecture

### Component Diagram

```
┌──────────────────────────────────────┐
│      scenarios.json (Input Data)     │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  1. ScenarioLoader (models.py)       │
│  - Parse JSON into Scenario objects  │
│  - Validate required fields          │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  2. Validator (validator.py)         │
│  - Check feasibility (battery range) │
│  - Identify infeasible buses         │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  3. ChargingPlanner (charging_planner.py) │
│  - Enumerate valid charging plans    │
│  - Use DFS for path finding          │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  4. Scheduler (scheduler.py)         │
│  - Greedy bus assignment             │
│  - Determine charging order          │
│  - Apply weighted objective          │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  5. Simulator (simulator.py)         │
│  - Simulate each bus's journey       │
│  - Track battery, time, wait times   │
│  - Validate feasibility              │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  6. MetricsEngine (metrics_engine.py) │
│  - Compute wait time totals          │
│  - Compute operator variance         │
│  - Compute weighted objective        │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  7. OutputFormatter (output_formatter.py) │
│  - Format per-bus timetables         │
│  - Format per-station queues         │
│  - Prepare for UI display            │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│      Streamlit UI (app.py)           │
│  - Display scenario input            │
│  - Display schedule output           │
│  - Allow scenario selection          │
└──────────────────────────────────────┘
```

### Component Responsibilities

**1. ScenarioLoader** (`loader.py`)
- Reads scenario JSON files
- Parses into typed Python objects (Bus, Route, Station, Scenario)
- Validates required fields and data types
- Returns structured Scenario object ready for scheduling

**2. Validator** (`validator.py`)
- Checks if a scenario is physically feasible
- Verifies no segment exceeds 240 km battery range
- Verifies route can be completed with available stations
- Returns early if infeasible (fail-fast)

**3. ChargingPlanner** (`charging_planner.py`)
- Enumerates all valid charging plans for each bus
- Uses depth-first search (DFS) to explore paths
- Marks plans as mandatory if only one exists
- Returns candidate plans for optimization

**4. Scheduler** (`scheduler.py`)
- Orchestrates the full scheduling pipeline
- For each bus: generate plans → simulate → assign
- Applies greedy strategy (sort by departure time, assign sequentially)
- Maintains station queues to track charger availability

**5. Simulator** (`simulator.py`)
- Simulates each bus's journey in detail
- Tracks position, battery state, time as bus travels
- At each charging station: computes wait time, adds 25-min charging, refills battery
- Returns ChargingAssignment with full timeline

**6. MetricsEngine** (`metrics_engine.py`)
- Computes total wait time across all buses
- Computes per-operator wait times and variance
- Computes network completion time (first departure to last arrival)
- Computes weighted objective: (individual × wait) + (operator × variance) + (overall × completion_time)

**7. OutputFormatter** (`output_formatter.py`)
- Formats per-bus timetables (human-readable, all events listed)
- Formats per-station queues (charging order, times)
- Formats metrics for display
- Prepares JSON-serializable output for Streamlit UI

**8. Streamlit UI** (`app.py`)
- Loads all scenarios from scenarios.json
- Provides scenario dropdown selector
- Displays scenario input (buses, route, stations, weights)
- On button click, runs full pipeline and displays results
- Shows metrics, per-bus timetables, per-station queues

## Data Model

### Core Objects (models.py)

```python
Bus
├── id: str                # "BUS-001"
├── operator: str          # "KPN", "Freshbus", "Flixbus"
├── direction: str         # "Bengaluru→Kochi" or "Kochi→Bengaluru"
├── departure_time: str    # "08:00" (HH:MM)
├── battery_range: int     # 240 km (per-bus, extensible)
├── priority: int          # 0-10 (for future priority rules)
└── metadata: dict         # Extensible for future use

Route
├── name: str              # "Bengaluru-Kochi"
├── segments: List[Segment]
│   ├── from_point: str
│   ├── to_point: str
│   ├── distance: int      # km
│   └── order: int         # Ensures linearity
└── endpoints: dict        # {"start": "Bengaluru", "end": "Kochi"}

Station
├── id: str                # "A", "B", "C", "D"
├── name: str              # "Station A"
├── location: str
├── chargers: int          # 1 (extensible to multiple)
├── charger_type: str      # "standard" (extensible to profiles)
└── metadata: dict         # For costs, location, etc.

ChargingPlan
├── bus_id: str
├── stations: List[str]    # Ordered station IDs
├── is_mandatory: bool     # True if only one valid plan
└── feasibility_reason: str

ChargingAssignment (Output)
├── bus_id: str
├── charging_plan: ChargingPlan
├── charging_events: List[ChargingEvent]
├── arrival_time: str
└── total_wait_time: int

Schedule (Final Output)
├── scenario_name: str
├── charging_assignments: List[ChargingAssignment]
├── station_queues: List[StationQueue]
├── metrics: Metrics
├── feasible: bool
└── validation_report: str
```

### Why This Design Supports Extensibility

1. **Per-Bus Fields**: Each bus has `battery_range` and `priority`, not global constants.
2. **Metadata Objects**: Bus, Station, and Scenario have `metadata: dict` for custom data without schema changes.
3. **Configurable Stations**: `chargers` field supports 1 or multiple chargers.
4. **Ordered Segments**: Route uses ordered segments, not implicit geometry, allowing multiple routes.
5. **Immutable Output**: Once a Schedule is created, it's not reassigned mid-pipeline.

## Algorithm: Greedy with Weighted Objective

### High-Level Approach

The scheduler uses a **greedy algorithm with weighted objective optimization** because:

- **Tractability**: The scheduling problem is NP-hard (similar to vehicle routing). Greedy is polynomial-time.
- **Interpretability**: Greedy decisions are easy to explain and debug.
- **Extensibility**: New rules can be added by modifying tie-breaking logic, not rewriting the engine.
- **Speed**: For 10-100 buses, greedy produces good solutions in milliseconds.

### Algorithm Steps

1. **Enumerate Charging Plans (per bus)**: Use DFS to find all valid paths through the route without exceeding 240 km between charges.

2. **Sort Buses**: Order buses by departure time to process them sequentially.

3. **For Each Bus**:
   - Generate candidate charging plans
   - Simulate the journey with each plan
   - Select the plan that minimizes the weighted objective
   - Update station queues with this bus's charging events

4. **Simulate Each Bus**: Track battery, time, and wait times as the bus travels. At each charging station, determine wait time based on current queue.

5. **Compute Metrics**: Calculate total wait time, operator variance, completion time, and weighted objective score.

### Weighted Objective Formula

```
score = (individual_weight × total_wait_time) +
        (operator_weight × operator_wait_variance) +
        (overall_weight × network_completion_time)
```

Operators adjust weights to change priorities:
- High `individual`: Minimize individual bus waits (fairness)
- High `operator`: Minimize variance between operators (fleet efficiency)
- High `overall`: Minimize total time (throughput)

## Extensibility Design: Adding New Features

### Pattern: Minimal Code Changes

Each extension uses the same pattern: **data + algorithm update + no core rewrite**.

### Extension 1: Multiple Chargers per Station

**Current State**: `Station.chargers = 1`

**Change Required**:
1. Update `scenarios.json`: Change `"chargers": 2` for any station
2. Update simulator: Modify `_compute_wait_time()` to check available chargers
3. **No core rewrite**: The rest of the pipeline remains unchanged

**Code Change**:
```python
# simulator.py
def _compute_wait_time(station, current_time, station_queues):
    available = station.chargers - len(station_queues.get(station.id, []))
    if available > 0:
        return 0  # Charger available immediately
    else:
        # Wait for earliest charger to free up
        queue = station_queues[station.id]
        return min(c['end_time'] for c in queue) - current_time
```

### Extension 2: Priority Buses

**Current State**: `Bus.priority = 5` (0-10 scale)

**Change Required**:
1. Update `scenarios.json`: Set `"priority": 9` for express buses
2. Update scheduler: Modify tie-breaking to prioritize high-priority buses
3. **No core rewrite**: Greedy algorithm unchanged, just tie-breaking updated

**Code Change**:
```python
# scheduler.py
# Sort buses by (priority desc, departure time asc)
sorted_buses = sorted(
    buses,
    key=lambda b: (-b.priority, b.departure_time)
)
```

### Extension 3: Time-of-Day Electricity Costs

**Current State**: `Station.metadata = {}`

**Change Required**:
1. Update `scenarios.json`: Add `"metadata": {"cost_per_minute": 0.5}`
2. Update metrics engine: Include cost term in weighted objective
3. **No core rewrite**: Data model already supports metadata

**Code Change**:
```python
# metrics_engine.py
for assignment in assignments:
    for event in assignment.charging_events:
        station = scenario.station_by_id[event.station_id]
        cost = station.metadata.get('cost_per_minute', 0) * 25
        total_cost += cost

metrics.weighted_objective += weights.cost * total_cost
```

### Extension 4: Driver Shift Constraints

**Current State**: `Bus.metadata = {}`

**Change Required**:
1. Update `scenarios.json`: Add `"metadata": {"driver_id": "D1", "max_shift": 480}` (480 min = 8 hours)
2. Add Validator check: Verify no driver exceeds max_shift_length
3. **No core rewrite**: Validation layer extended, scheduler unchanged

**Code Change**:
```python
# validator.py
def validate_driver_shifts(scenario):
    for bus in scenario.buses:
        if 'driver_id' in bus.metadata:
            max_shift = bus.metadata.get('max_shift', 480)
            # After simulation: check if shift_length > max_shift, raise error
```

### Extension 5: New Operators

**Current State**: `Bus.operator = "string"`

**Change Required**:
1. Update `scenarios.json`: Use new operator name in bus data
2. **No code change**: Operators are identified by string, handled dynamically
3. Metrics engine automatically computes per-operator metrics for any operator

### Extension 6: Multiple Routes

**Current State**: `Route` is a single object

**Change Required**:
1. Update `scenarios.json`: Add route name and parameterize segments
2. Update Scenario: Support multiple Route objects (optional for MVP)
3. **No core rewrite**: Route model already supports naming and parameterization

## Key Design Decisions & Trade-Offs

### Why Greedy, Not Constraint Programming?

**Decision**: Use greedy algorithm with simulation-based validation

**Alternatives Considered**:
- Constraint Programming (OR-Tools, Gurobi): Finds optimal solutions but requires external dependencies, harder to extend with custom rules
- Simulated Annealing: Better quality than greedy but slower, harder to explain decisions
- Genetic Algorithms: Highly customizable but slow and unpredictable

**Trade-Off**: Greedy is fast and transparent, making it ideal for learning and interview discussion. If optimality becomes critical, the algorithm can be replaced later without changing the data model or interfaces.

### Why Simulation-Based Validation?

**Decision**: Simulate each bus's journey to compute timelines and validate feasibility

**Alternatives Considered**:
- Algebraic validation: Faster but less reliable for complex scenarios with interdependencies
- Constraint checking: Harder to debug and explain

**Trade-Off**: Simulation is slightly slower but provides ground truth. Operators trust the schedule because it's been validated through detailed simulation.

### Why Data-Driven Weights?

**Decision**: Store weights in scenario JSON, not code

**Alternatives Considered**:
- Hardcode weights in scheduler: Faster development but inflexible, requires code changes to experiment
- Parameter objects: More flexible but adds complexity

**Trade-Off**: Data-driven weights are slightly slower to parse but allow operators to experiment without touching code.

## Testing Strategy

### Property-Based Correctness

Each correctness property is implemented as a unit test or property-based test (minimum 100 iterations):

1. **Scenario Parsing Round Trip**: JSON → Scenario → JSON produces equivalent result
2. **Missing Field Detection**: Missing required fields are caught
3. **Feasibility Validation**: Infeasible scenarios detected early
4. **Battery Constraint**: No bus exceeds 240 km between charges
5. **Single-Charger Constraint**: No two buses charge at same station same time
6. **Weighted Objective**: Changing weights produces different schedules
7. **Tie-Breaking Consistency**: Same inputs produce same outputs
8. **Output Feasibility**: Final schedule passes all validation checks

### Scenario-Based Testing

Test the 5 provided scenarios:

1. **Scenario 1** (Even Spacing): Baseline, minimal contention
2. **Scenario 2** (Bunched Start): Heavy early contention
3. **Scenario 3** (Asymmetric Load): Uneven traffic
4. **Scenario 4** (Operator Heavy): Operator prioritization
5. **Scenario 5** (Worst Case): Maximum collision

## Assumptions

1. **Constant Travel Speed**: 60 km/h (configurable globally, not per-bus in MVP)
2. **Fixed Charging Time**: 25 minutes always
3. **Uniform Battery**: 240 km range (configurable per-bus)
4. **Linear Route**: No backtracking or alternatives
5. **Deterministic Departures**: Buses leave on time (no delays)
6. **Single Charger per Station** (initially; extensible to multiple)
7. **Greedy Suffices**: For MVP, greedy is fast enough

## How to Change a Weight (Example)

Edit `scenarios.json`:

```json
{
  "scenario_4": {
    "name": "Scenario 4 - Operator Heavy",
    "buses": [...],
    "weights": {
      "individual": 1.0,
      "operator": 2.0,      // Changed from 1.0 to 2.0
      "overall": 1.0
    }
  }
}
```

Run the app. The scheduler automatically uses the new weights—no code change needed.

## How to Add a New Rule (Example: Express Buses)

1. **Update Bus model** (`models.py`):
   ```python
   @dataclass
   class Bus:
       priority: int = 5  # Already included
   ```

2. **Update scheduler tie-breaking** (`scheduler.py`):
   ```python
   sorted_buses = sorted(
       buses,
       key=lambda b: (-b.priority, b.departure_time)  # Higher priority first
   )
   ```

3. **Update scenarios.json**:
   ```json
   {"id": "express-01", "priority": 9, ...}  // 9 = high priority
   ```

4. **Test**: Run app, verify express buses charge first at contended stations.

**Result**: Express buses are prioritized without rewriting the core scheduler logic.

## Deployment

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Community Cloud (Recommended)
1. Push code to GitHub (public repo)
2. Go to https://share.streamlit.io
3. Connect GitHub repo
4. Deploy instantly

No Docker, no infrastructure, no cost.

## Summary

This architecture prioritizes:
- **Clarity**: Each component has one job
- **Extensibility**: Future changes mostly require data updates
- **Speed**: Greedy algorithm is fast, simulation validates correctness
- **Transparency**: Greedy decisions are easy to explain in interviews
- **Scalability**: Modular design allows replacing components (e.g., greedy → constraint solver) without touching others

The design has been tested across 5 scenarios spanning minimal to worst-case contention, proving robustness and extensibility.
