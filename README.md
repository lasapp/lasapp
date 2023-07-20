<img src="lasapp_logo.png">

# Language-Agnostic Static Analysis for Probabilistic Programs

Replication package for ICSE 2024 submission with the same name.

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
python3 icse24/main.py -h
usage: main.py [-h] [-a A] program_name ppl

positional arguments:
  program_name  motivating | linear_model | slicing | pedestrian | constraint | guide
  ppl           turing | gen | pyro | pymc | beanmachine

options:
  -h, --help    show this help message and exit
  -a A          graph | hmc | constraint | guide
  -v            if set source code of file will be printed
```

Omitting the `-a` argument will analyse the program as in the reference paper.

But you can use all presented analyses:
- `-a=graph` model graph extraction
- `-a=hmc` HMC assumption checker
- `-a=constraint` parameter constraint verification
- `-a=guide` model-guide validation

All example programs that are analysed can be found at `icse24/examples`.

The `guide` analysis is only available for the `guide` program in `gen` and `pyro`.

The `pedestrian` model is not available in `pymc`.

```
# stop language servers
./scripts/stop_servers.sh
```

### Replication of Paper
Start the language servers and verify that they running.

#### Motivating example (Figure 3): Catching discrete variables.
```
python3 icse24/main.py motivating turing
python3 icse24/main.py motivating beanmachine
python3 icse24/main.py motivating pyro
```
Also available for `gen`, and `pymc`.

#### Model graph extraction (Figure 6):
```
python3 icse24/main.py slicing turing
```
Check out the plot by running on the host machine:
```
docker cp lasapp:/LASAPP/tmp/model.gv.pdf . && open model.gv.pdf
```
Also available for `gen`, `pyro`, `pymc`, and `beanmachine`.

#### HMC Assumption Checking for Pedestrian Model (Figure 7):
```
python3 icse24/main.py pedestrian pyro
```
Also available for `gen`, `turing`, and `beanmachine`.

#### Parameter Constraint Verification (Figure 8):
```
python3 icse24/main.py linear_model pymc
python3 icse24/main.py constraint gen
```
Also available for `turing`, `gen`, `pyro`, `pymc`, and `beanmachine`.

#### Model-Guide Validation (Figure 9):

```
python3 icse24/main.py guide pyro
```
Also available for `gen`.

## Writing Analysable Programs

In this prototype we provide initial implementations of the language servers.

Therefore, we rely on a few assumptions and the analysis may crash for some programs.

Take a look at `icse24/examples`  and `examples/` for some reference programs.

Generally, the analyses are most robust for programs written in a "Static Single Assigment" like fashion.

We list some of the assumptions of the language servers / program analyses:
- Multiple files not supported.
- Sample statements should be assigned to program variable and not used directly:
  - ok:
  ```
  m = pyro.sample("m", dists.Normal(0.,1.))
  x = pyro.sample("x", dists.Normal(mu,1.))
  ```
  - not ok:
  ```
  x = pyro.sample(pyro.sample("m", dists.Normal(0.,1.)), dists.Normal(mu,1.))
  ```
  Will be improved in the future.
- The address in sample statements should be consistent.
  - `:x => i` or `f"x_{i}"` are supported but cannot be matched to `:x => j` or `f"x_{j}"`
- Julia:
  - No struct, let, macro, do.
- Turing:
  - Model specified by `@model function model(...)` or `@model function <name>(...)`, where `model = <name>` is a top-level assignment.
- Gen:
  - Model specified by `@gen function model(...)` or `@gen function <name>(...)`, where `model = <name>` is a top-level assignment.
  - Observations are defined at the top-level by `observations = choicemap(address => value)` and/or `observations[address] = value`
- Pyro:
  - Model specified by `def model(...)` or `def <name>(...)`, where `model = <name>` is a top-level assignment.
- PyMC:
  - Model specified by `with pm.Model() as model` or `with pm.Model() as <name>`, where `model = <name>` is a top-level assignment.
- BeanMachine
  - All declared random variables belong to the model.
  - Observations are defined at the top-level by `observations = {address: value}` and/or `observations[address] = value`
- Distributions:
  - All parameters are provided. No default parameters.
  - PyMC / torch.distributions: `logits` parameters not supported
- Data and Control Flow:
  - no structs / classes
  - No break / continue control flow.
  - No try / catch / finally blocks.
  - Functions are pure: no side effects / same output for same arguments (no closures), no outside dependence
  - works best with static single assignments
- Symbolic Evaluation:
  - no loops
  - no arrays
  - supports: `+, -, *, /, ^, &, |, !, ==, !=, >, >=, <, <=`
- Interval Arithmetic:
  - no loops
  - expression for which interval should be calculated can be computed by following simple assignments (no complex control flow)
  - supports:  `+, *, -, /, exp, log, sqrt, ^{float}, min, max, ifelse (pytensor)`
  - all elements of array are estimated with single interval
- Paramter Constraint Verification:
  - univariate random variables with interval support
- Model/Guide Validation:
  - One model function and one guide definition.
