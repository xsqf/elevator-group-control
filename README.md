# Orrery

**or·rer·y** /ˈôrərē/\
▸ noun\
a clockwork model of the solar system.

## Project description

Orrery is a configurable model of an elevator system. It simulates Elevator Group Control scenarios.

The project prompt is provided in [this README.md](https://github.com/jknehr/recruiting/tree/master/elevator).

## Project status

* This is a demo of WIP as of 04/18/2024.
* It contains hardcoded values for the purpose of demoing.
* It contains pseudocode to give a picture of WIP for the current sprint.
* A full working knowledge repository containing research, works cited, design, task planning, and daily timeline of work accomplished is actively maintained in my personal Notion workspace (shared on request).

## Next steps

* post-mortem / retrospective
* selection of features from roadmap for subsequent sprint

# Usage

Requires Docker ([Docker Desktop install recommended](https://docs.docker.com/desktop/)).

```
make build
make sim
```

## Interactive

```
make build
make run-shell
python orrery/simulator.py
```

# Design

## Philosophy
* "open to extension, closed to modification"
  * seek the simplest path to base requirements while maintaining maximum extensibility
  * do not compromise best practices in pursuit of functionality
* event simulator fidelity
  * this is the most core aspiration of the project
  * built correctly, this framework could be used for many manners of discrete event simulation for a variety of closed systems
* state transformation fidelity and modularity
  * modular embedded decision rules (i.e., scheduling algorithm)
  * controller must be algorithm agnostic
* state tracking fidelity
  * tracking of decision epochs and embedded decision rules
  * tracking of system transforms
  * tracking of system state in universal format for database and API access
* profiling
  * tracking of all simulation runs
  * tracking of standardized statistics as KPIs for all simulation runs
* testing
  * tests should confirm you haven’t broken anything when you change the controller logic or simulator architecture
  * tests are for business rules and expectations of success
  * unit tests are for verifying atomic outcomes and object behavior
* "dodge"
  * seeking the perfect heuristic
  * ignoring hidden costs of implementation

## Product requirements

These are the targets I’d present to the Product Team requesting this system. These requirements were not provided, so I researched and selected targets from industry best-practice benchmarks.

1. Real-time compliance: Elevator assignment issued within one second of request
    1. i.e., offline subproblem average solve time is ≤ 1 second computation time on consumer-grade personal machine
2. Satisfactory SLAs: (simplification 1 step ≣ 1 sec)
    1. Excellent Wait SLA:
        1. 98% of passenger wait times < 60 seconds
        2. 75% of passenger wait times < 30 seconds
        - “It is recommended that for an excellent service level in office buildings
        98 percent of all waiting times should be less than 60 seconds and
        75 percent less than 30 seconds (Barney, 2003)” ([source](https://doi.org/10.1016/j.ejor.2016.01.019), citing Al-Sharif & Barney “Elevator Traffic Handbook”)

    2. Satisfactory Time-to-Destination SLA:
        1. ≤ 100 seconds ([source](https://www.notion.so/Works-cited-60782573c06f43bf9d473508e67b1f81?pvs=21), citing Otis elevator company)
3. Reversal control: Passenger travel is unidirectional (i.e., no reverse journeys)
4. Behavior profiling: Key system metrics are tracked for every model run
    1. “[Time]’s measurement is critical to building a successful system.”
    2. To measure whether feature changes improve or degrade model performance
5. Modular processor: Proper system functionality is scheduling algorithm agnostic
    1. Processor accommodates extensible injection of verifiable scheduling behavior

## Primary objectives

1. All requests picked up.
2. All requests dropped off at target floor.
3. Minimize average `total time` = `caller wait time` + `elevator travel time to destination floor`.
    - challenging because optimization has exponential complexity O(C^N)
    - want to get to a more favorable low order polynomial complexity instead
4. Console immediately tells passenger which elevator number to wait for.
5. Passenger destination floor assignment cannot be changed while in the elevator.
6. Elevator system must react to requests as they enter the system.

## Design requirements

- `README.md`
    - explains how to run the solution
    - short discussion of assumptions, simplifications, trade-offs
- scheduling algorithm of your choice
- configurable parameters (total #)
    - elevators
        - n.b.: for any waiting number of passengers *n*, total assignments are c^n, explodes
    - building floors (number of floors)
    - elevator capacity (max passengers per car)
- Type 2 system (full destination control, a.k.a. Destination Dispatch System)
    - origin floor and target floor available to system upon passenger request
- “Function for your model”
    - input: list of requests with fields
        1. request time (integer from 0 to infinity)
        2. ID (string identifier for passenger)
        3. source floor (integer between 1 and n, num of floors)
        4. target floor (integer between 1 and n, num of floors)
        - time can be specified more than once in the request list but always increases
        - input format requirement not provided
            - self-specify
            - load from CSV
    - exit once all input requests have been processed by the system AND all passengers have been delivered to their final destination floors
    - output: state + statistics
        1. States - what floor each elevator is at for every point in time to a file (i.e., tick time forward by 1 unit in continuous fashion logging locations of each elevator in the system at all times)
        2. Summary Stats - write out summary statistics for min, max, and mean `total time` and `wait time` for all passengers. “Have a look at the full distribution - what information stands out to you?”

### Statistics

These are the statistics I would suggest enforcing tracking for profiling across simulations.

- Passenger Waiting Time
- Average Waiting Time
- Passenger Transit Time
- Average Transit Time
- Passenger Sojourn Time
- Average Sojourn Time

# Assumptions, simplifications, and tradeoffs

- discrete state space (i.e., incremental time instead of continuous time)
- incremental time unit is "unitless" (i.e., not a second, just a unit)
- hall call queues have infinite capacity
- one elevator per shaft
- all shafts serve all floors
- (per instructions) no lookahead
    - i.e., destination dispatch system at time t_i is aware only of requests made and fulfilled from time t_0 to t_i
- no precedence constraint on hall calls
    - unassigned requests may be assigned in any order (no FIFO)
- passenger arrivals are [Poisson arrivals](https://www.sciencedirect.com/topics/mathematics/poisson-arrival) (Poisson distributed w/ known random seed, generated randomly with exponentially distributed inter-arrival times)
- passenger origin and destination floor are never the same
- full configuration destination dispatch system (i.e., destination hall call panels on all floors)
- all elevators begin at floor 1 (i.e., initial idling state at what would be considered “lobby”) but here is simply lowest / 1-indexed
- requests can originate from any floor of the building, does not require that everyone “enters” on lobby at start of simulation
- simulation starts at zero occupancy
- no zoning
    - no dynamic allocation
        - no express / local distinction
- inter-floor distances are all the same
- rate of travel is identical for all elevators
- time to travel is identical across all floors (1 unit time / floor)
- all elevators have same capacity (persons occupancy)
- instantaneous acceleration
- does not account for door opening, door closing delay time, or door closing time
    - ignores any ability for passengers aboard or in elevator lobby to hold the doors for passengers
- all hall calls made instantly and simultaneously at each point in time
- immediate assignment (i.e., instantaneous or realistically within 1 sec computation)
    - new information after elevator assignment doesn’t alter passenger-elevator assigned
- immutable assignment (i.e., preassignment constraint)
- passengers board instantaneously (elevator lobby size and panel distribution ignored)
- passengers deboard only upon arrival at their intended floor (i.e., no pre-emption, make only one “trip”)
- one passenger per hall call (instead of one request for group of passengers, which in the real world is frequently the case at lunch hour of colleagues departing together)
- one hall call per intended transit
    - i.e., never more than one hall call from passenger due to forgetfulness or impatience
- perfect compliance to elevator assignment (i.e., one occupant per hall call)
    - does not account for passenger missing their elevator and failing to board
    - does not account for passengers boarding different elevator than assigned that stops on their floor if it happens to be going to their desired destination
    - eliminating perfect compliance would mandate occupancy sensing instead of simple logic based on capacity to maintain optimality constraints of capacity
- all passengers identical in size / weight / ability / possessions ([NIOSH on anthropometry](https://www.cdc.gov/niosh/topics/anthropometry/default.html))
    - ignores impact of passenger anthropometrics and their possessions vary and impact occupancy limits
    - e.g., passengers with wheelchairs, walkers, strollers, packages, dollies, bell carts, etc.
- no occupancy sensing, per assumption of perfect compliance in lieu of real-time capacity
- no quality of service or saturation avoidance requirements
    - important to avoid saturation, but no guarantees made of adherence to permissible level
    - no re-prioritization of hall call in queue when wait time exceeds permissible level
- elevators operate continuously and indefinitely (i.e., no maintenance or SLA compromises)
- no reversal control and no minimization of reverse journeys
    - i.e., lobby could have basement floors
- ties between elevator assignment are broken round-robin, should they ever occur

### Aspirational tradeoff

I had to recognize trading off the optimal solution as aspirational at this point in time.

- need a fast offline optimization module to provide reasonable or near-optimal dispatch plan in less than a second
    - exact algorithms unreliable to meet real time requirements at scale
    - heuristic algorithms reasonable but can’t guarantee optimality
- [heuristic integrated reoptimization policies](https://www.sciencedirect.com/science/article/pii/S0166218X06001466#:~:text=4.3.2.%20Heuristic%20reoptimization%20policies) (most prominently REOPT-BESTINSERT, REOPT-TWOOPT)
    - “at the arrival at each new request a static multi-elevator dispatching problem is constructed. The input for this offline optimization problem is the current state of the system”
    - policy solves problem by heuristic means, i.e., does not give any information about optimality gap of the solution obtained
    - integrated = assignment decisions + scheduling decisions


# Roadmap

* Milestone 0.1.0 satisfying all aspects of prompt requirements

## Opportunities for enhancement

### Technical

- Penalize wait time exponentially beyond permissible SLA, use this in objective function
- Extend test coverage & logging
- Verbose debugger
- Evaluate backwards compatibility - https://github.com/tox-dev/tox for Python
- Extend run metrics logging & profiling
- additional classes for `simulation` / `model` , numerous benefits
    - more robust Discrete-Event Simulation model, perform Monte Carlo simulations to get tighter confidence interval on performance over large / long sample spaces and times
    - multiple simulations at once, then compare
    - determine champion / challenger
- learn applied mathematics and ops research to get a grasp on IP/LP generally, and Dantzig-Wolfe decomposition & column generation specifically
- simple [branch and bound](https://en.wikipedia.org/wiki/Branch_and_bound) solution approach
- branch-cut-and-price
- algorithms [REOPT-BESTINSERT or REOPT-TWOOPT](https://www.sciencedirect.com/science/article/pii/S0166218X06001466#:~:text=More%20formally%2C%20at,optimization%20can%20do.)
    - [REOPT-ZIBDIP] from that team's prior research
    - Dynamic Pricing Control (their custom-made dynamic [column
    generation](https://en.wikipedia.org/wiki/Column_generation) method) provides rapidly converging column generation procedure
    - solves the linear programming [relaxation](https://en.m.wikipedia.org/wiki/Linear_programming_relaxation) (LP) of integer programming (IP) by dynamic column generation (custom pricing, search tree = [depth-first-search](https://www.codecademy.com/resources/docs/ai/search-algorithms/depth-first-search) branch&bound tree) in set partitioning formulation of the problem
    - during high load, [10% lower average waiting time vs two REOPT above](https://www.sciencedirect.com/science/article/pii/S0166218X06001466#:~:text=The%20exact%20reoptimization%20methods,WOOPT.) ([badass paper](https://www.sciencedirect.com/science/article/pii/S0166218X06001466) and its [prequel](https://link.springer.com/chapter/10.1007/3-540-45749-6_56))
- multi-objective optimization (discrete variables, genetic algorithm)
  - [example optimization using genetic algorithm in Python](https://elevatorworld.com/article/)
- Estimated-Time-of-Arrival (ETA) algorithm evaluation for potential performance improvements (see research)
- of course, can always line-profile the Python repository itself

### Functional

- group function
    - hall call specifies # of passengers instead of assuming 1 passenger per hall call
- traffic epochs
    - time of day or request volume informs algorithm / rule engine choices
- up-peak sectoring
    - dynamic sectoring / zoning
    - dynamic allocation (i.e., elevators are not affixed to a sector across all round trips, can change each round trip)
        - sequencing / rotation of elevator assignment between sectors
- inform choice of optimization function
    - passenger satisfaction / preferences
        - minimize journey time
        - minimize wait time
            - see [psychology of waiting](https://peters-research.com/index.php/2020/11/17/a-review-of-waiting-time-journey-time-and-quality-of-service/) paper
        - minimize total transit time
        - reverse journey considerations (see research)
    - operator satisfaction / preferences
        - minimize energy usage
        - minimize distance traveled
        - minimize stops made (decreases wear-and-tear)
        - plan servicing schedule to uphold SLA with minimal disruption
- add more realistic physics to incremental time (e.g., acceleration, door delay, etc.)
- special functionality for specific passengers
    - passengers with disabilities (”handicap mode”)
        - may change allocation behavior to send lowest occupancy elevator instead of standard, in consideration that passengers with disabilities potentially need additional room and/or time to board (e.g., may use a wheelchair / powerchair, have a service animal with them, or an interpreter or caretaker with them)
        - extends door closing delay time (currently ignored in initial implementation)
        - assigns adjacent elevator to request terminal when possible (currently ignored)
        - emergency function
            - in case of emergency, system remembers drop-off floor of passengers who indicated they are an individual with disability, sends elevators, and holds there
            - passengers with limited mobility need the assistance of elevators to evacuate if required in the case of an emergency
            - dispatching and/or capacity limits should be modified in response to this
        - see literal compliance (e.g., ADA, [ICC/ANSI A117.1.2003](https://codes.iccsafe.org/content/icca117-12003/chapter-1-application-and-administration), European standard [EN 81-70:2021+A1:2022](https://standards.iteh.ai/catalog/standards/cen/d545a2e8-e577-4b63-97ac-b73fb24920ca/en-81-70-2021a1-2022))
    - priority passengers / behavior override
        - Chief of Staff or Executive Assistant with special privileges
        - first responders, obviously
        - send empty car
        - non-stop travel
- real-time occupancy sensing (discards assumptions and accounts for actual behavior)
    - commercial offering from Abacus, see [whitepaper](https://uploads-ssl.webflow.com/5fb4004807f29431d9c84a6f/61770276f091c776d92edcbc_Abacus%20Whitepaper.pdf)
    - increased relevance due to recent pandemic and redefinitions of occupancy limit
    - accounts for passenger anthropometric diversity
    - accessibility component
- discover new features
    - consult the literature to discover new state-of-the-art features to evaluate placement in roadmap, starting with [industry leading knowledge repositories](https://www.notion.so/Elevator-Sources-8407b16901d4412bbbf79a229b6df3f8?pvs=21)
    - consult leading textbooks
        - Elevator Traffic Handbook (Barnes), for one
    - study industry leaders
        - Otis (U.S.)
        - ThyssenKrupp (Germany), now TK Elevators
        - Kone (Finland)
        - Schindler (Switzerland)
        - Mitsubishi
            - Electric Europe (Belgium)
            - Heavy Industries (Japan)
