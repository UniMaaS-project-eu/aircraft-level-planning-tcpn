# Aircraft Level Planning tCPN

This is an implementation of the timed Colored Petri Net that models the Aircraft Level Planning problem.

## Installation: 
- inside the cloned directory of this repo run:
```
cd cpn-py
pip install -e .
```
## Usage:

```
usage: python vp1.py [-h] [-v] [-o FILE] [-j] [-i] [-x] [--interactive_viewer] [-q] mode

positional arguments:
  mode                  manual|sim|statespace

options:
  -h, --help            show this help message and exit
  -v, --verbose         print additional step statuses
  -o FILE, --file FILE  select initial marking json file
  -j, --no_json         do not generate json
  -i, --no_img          do not generate images
  -x, --no_nx           do not generate networkx representation of state space graph(statespace mode only)
  --interactive_viewer  launch interactive viewer that displays generated state space graph(statespace mode only)
  -q, --quiet           do not display steps/markings
```

### Manual Mode:
Runs a simulation of the Petri Net step by step
### Simulation Mode:
Runs a simulation of the Petri Net until deadlock is detected

### Statespace Mode:
Generates state space graph


## Generate Marking from provided dataset:
You can use the `dataset_to_json.py` script to generate initial marking from the provided real datasets.
```
usage : python dataset_to_json.py DAYS

positional arguments:
  DAYS                  number of days in the simulation period


```