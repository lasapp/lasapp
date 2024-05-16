<img width=600px, src="lasapp_logo.png">

# Language-Agnostic Static Analysis of Probabilistic Programs

Replication package for submission with the same name.

The full implementation of the four language-agnosic analyses can be found in `src/static/analysis`.

The LASAPP front-end API is implemented in `src/static/lasapp`.

The Julia language server can be found in `src/jl` and the Python language server can be found in `src/py`.

The classical analysis backbone is located in `src/jl/analysis` and `src/py/analysis`.

## Setup

Installation with Docker is recommended.

### Docker Installation

Install [docker](https://www.docker.com).

```
docker build -t lasapp .
docker run -it --name lasapp --rm lasapp
```

### Manual Installation

Requirements:
- Unix-based operating system
- Python 3.10.12
- Julia 1.9.2
- tmux
- [graphviz](https://www.graphviz.org)
  
Install packages:
```
pip install -r src/py/requirements.txt
julia --project=src/jl -e "using Pkg; Pkg.instantiate();"
```

### Test Installation
```
./scripts/test_servers.sh
```

```
# start language servers
./scripts/start_servers.sh
```

```
# verify that language servers are running
tmux ls
tmux attach -t ls-jl
tmux attach -t ls-py
```
(detach with `Ctrl+b d`)

```
python3 src/static/test/all.py
```


## Usage

```
# start language servers if not started already
./scripts/start_servers.sh
```
Run main file:
```
python3 main.py -h
usage: main.py [-h] [-a A] [-v] filename

positional arguments:
  filename    path to probabilistic program

options:
  -h, --help  show this help message and exit
  -a A        graph | hmc | constraint | guide-proposal | guide-svi
  -v          if set source code of file will be printed
```

You can use all static analyses:
- `-a=graph` model graph extraction
- `-a=hmc` HMC assumption checker
- `-a=constraint` parameter constraint verification
- `-a=guide-proposal` model-guide validation (model >> guide)
- `-a=guide-svi` model-guide validation (guide >> model)

Example programs can be found at `experiments/examples`.
```
# stop language servers
./scripts/stop_servers.sh
```

## Replication of Paper
Start the language servers and verify that they are running.
```
# start language servers if not started already
./scripts/start_servers.sh
```
### Evaluation

Statistical Dependency Analysis (Model Graph) and Parameter Constraint Analysis
```
python3 experiments/evaluate_graph_and_constraints.py
```

HMC Assumption Analysis
```
python3 experiments/evaluate_hmc.py
```

Model-Guide Validation Analysis
```
python3 experiments/evaluate_guide.py
```

With the model graph analysis we have identified a bug in <evaluation/turing/statistical_rethinking_2/chapter_14_6.jl>.

### Some additional examples

#### Motivating example (Figure 3): Catching discrete variables.
```
python3 main.py experiments/examples/motivating_turing.jl -a hmc
python3 main.py experiments/examples/motivating_beanmachine.py -a hmc
python3 main.py experiments/examples/motivating_pyro.py -a hmc
```
Also available for `gen`, and `pymc`.

#### Model graph extraction (Figure 6):
```
python3 main.py experiments/examples/pedestrian_turing.jl -a graph
```
Check out the plot by running on the host machine:
```
docker cp lasapp:/LASAPP/tmp/model.gv.pdf . && open model.gv.pdf
```
Also available for `gen`, `pyro`.

#### HMC Assumption Checking for Pedestrian Model:
```
python3 main.py experiments/examples/pedestrian_pyro.py -a hmc
```
Also available for `gen`, `turing`, and `beanmachine`.

#### Parameter Constraint Verification (Figure 7):
```
python3 main.py experiments/examples/constraint_gen.jl -a constraint
```
Also available for `turing`, `gen`, `pyro`, `pymc`, and `beanmachine`.

#### Model-Guide Validation:
```
python3 main.py experiments/examples/guide_pyro.py -a guide-proposal
```
Also available for `gen`.
