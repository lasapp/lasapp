<img width=600px, src="lasapp_logo.png">

# Language-Agnostic Static Analysis of Probabilistic Programs

Replication package for ASE2024 paper with the same name.

Overview:
```
.  
├── evaluation/                                     # Probabilistic Program Benchmark Dataset
│     ├── gen/                                      # 8 Gen.jl programs with discontinuous density
│     ├── pymc/                                     # 97 PyMC programs sourced from [pymc-resources]
│     ├── pyro/                                     # 8 Pyro programs with model-guide pairs sourced from [wonyeol]
│     └── turing/                                   # 117 Turing.jl programs sourced from [SR2TuringPluto.jl] and [TuringTutorials]
│
├── experiments/                                    # Scripts to reproduce results of paper
│     ├── examples/                                 # Some probabilistic programs featured as examples in the paper tranlsated to several PPLs
│     ├── evaluate_graph_and_constraints.py         # Script to reproduce Dependency Analysis and Constraint Verifier experiments for PyMC and Turing
│     ├── evaluate_guide.py                         # Script to reproduce Model-Guide Validator experiment for Pyro
│     └── evaluate_hmc.py                           # Script to reproduce HMC Assumption Checker for Gen
│
├── scripts/                                        # Scripts to start, stop, and test language servers
│     ├── start_servers.sh                          # Start Python and Julia language server
│     ├── stop_servers.sh                           # Stop Python and Julia language server
│     └── test_servers.sh                           # Test Python and Julia language server
│
├── src/                                            # LASAPP source code
│     ├── jl/                                       # Julia language server
│     │     ├── analysis/                           # Julia classical analysis backend
│     │     ├── ast/                                # AST utilities
│     │     ├── ppls/                               # Julia PPL bindings
│     │     │     ├── distributions.jl              # Distributions.jl distribution backend
│     │     │     ├── gen.jl                        # Gen.jl bindings
│     │     │     └── turing.jl                     # Turing.jl bindings
│     │     └── test/                               # Unit tests
│     └── py/                                       # Python language server
│     │     ├── analysis/                           # Python classical analysis backend
│     │     ├── ast_utils/                          # AST utilities
│     │     ├── ppls/                               # Python PPL bindings
│     │     │     ├── beanmachine.py                # BeanMachine bindings
│     │     │     ├── pymc.py                       # PyMC bindings
│     │     │     ├── pyro.py                       # Pyro bindings
│     │     │     └── torch_distributions.py        # PyTorch distributions backend
│     │     └── test/                               # Unit tests
│     └── static/                                   # Static analysis front-end
│           ├── analysis/                           # Python classical analysis backend
│           │     ├── constraint_verification.py    # Parameter Constraint Verifier (Section 4.4)
│           │     ├── guide_validation.py           # Model-Guide Validator (Section 4.5)
│           │     ├── hmc_assumption_checker.py     # HMC Assumptions Checker (Section 4.3)
│           │     └── model_graph.py                # Statistical Dependency Analysis (Section 4.2)
│           ├── lassap/                             # LASAPP framework front-end
│           └── test/                               # Unit tests
│ 
├── Dockerfile                                      # File for building Docker image  
└── main.py                                         # Script to apply any analysis to probabilstic program in file
```

Data sources:
- [[pymc-resources]](https://github.com/pymc-devs/pymc-resources/tree/a5f993653e467da11e9fc4ec682e96d59b880102)
- [[wonyeol]](https://github.com/wonyeol/static-analysis-for-support-match/tree/850fb58ec5ce2f5e82262c2a9bfc067b799297c1/tests/pyro_examples)
- [[SR2TuringPluto.jl]](https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80)
- [[TuringTutorials]](https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648)

## Setup

No special hardware is needed for installation.

Recommendations:
- Hardware: >= 3.5 GHZ dual core CPU, >= 8 GB RAM, and >= 10 GB storage
- OS: unix-based operating system
- Installation with Docker

### Docker Installation

Install [docker](https://www.docker.com).

Build the lasapp image (this may take several minutes):
```
docker build -t lasapp .
```

If the build was successful, run the docker image:
```
docker run -it --name lasapp --rm lasapp
```

### Manual Installation

Requirements:
- Unix-based operating system
- Python 3.10.12
- Julia 1.9.2
- tmux
- [graphviz](https://www.graphviz.org)
- [Z3](https://github.com/Z3Prover/z3)
  
Install packages:
```
pip install -r src/py/requirements.txt
julia --project=src/jl -e "using Pkg; Pkg.instantiate();"
```

### Test Installation

To test the installation, first we run test scripts for both the Julia and Python language server.
```
./scripts/test_servers.sh
```
(If for some reason a segmentation error is reported run the tests individually: `julia --project=src/jl src/jl/test/all.jl` `python3 src/py/test/all.py`)

If all tests pass, you can start the language servers:
```
# start language servers
./scripts/start_servers.sh
```

```
# verify that language servers are running
tmux ls
```
You should see two instances `ls-jl` and `ls-py`.

If you like, you can attach to the servers with one of the following commands and detach with `Ctrl+b d`.
However, this is not required.
```
tmux attach -t ls-jl
tmux attach -t ls-py
```

Run the test file.
```
python3 src/static/test/all.py
```
If there are no errors (result is OK), installation was successful.

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
  --v         if set, source code of file will be printed
  --view      Only applicable for -a graph. If set, model graph will be plotted and displayed. Otherwise, only saved to disk.
```

You can use all static analyses:
- `-a=graph` model graph extraction
- `-a=hmc` HMC assumption checker
- `-a=constraint` parameter constraint verification
- `-a=guide-proposal` model-guide validation (model >> guide)
- `-a=guide-svi` model-guide validation (guide >> model)

Example programs can be found at `experiments/examples`.

Usage examples can be found below.

After you are finished, you may stop the language servers.
```
# stop language servers
./scripts/stop_servers.sh
```

## Reproducing the Results of the Paper (Section 5 / Table 2)
Start the language servers and verify that they are running.
```
# start language servers if not started already
./scripts/start_servers.sh
```
### Evaluation

Statistical Dependency Analysis (Model Graph) and Parameter Constraint Analysis
```
python3 experiments/evaluate_graph_and_constraints.py -ppl turing
```
This will perfrom the Statistical Dependency Analysis and the Parameter Constraint Verifier for 117 Turing programs.  
For each program, the result will be printed: Everything is ok = correct, Warnings produced = unsupported.  
At the end, the summary counts are reported.

```
python3 experiments/evaluate_graph_and_constraints.py -ppl pymc
```
Performs the same experiment for 97 PyMC programs.

HMC Assumption Analysis
```
python3 experiments/evaluate_hmc.py
```
Performs the HMC Assumption Checker for 8 Gen programs.  
For each program, the result will be printed: Everything is ok = false negative, Warnings produced = true positive.  


Model-Guide Validation Analysis
```
python3 experiments/evaluate_guide.py
```
Performs the Model-Guide Validation Validator for 8 Pyro programs.  
For each program, the result will be printed: Everything is ok = true negative, Warnings produced = true positive.  

Note: With the model graph analysis we have identified a bug in <a href="evaluation/turing/statistical_rethinking_2/chapter_14_6.jl">chapter_14_6.jl</a>.

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
