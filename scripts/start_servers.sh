#!/bin/bash
tmux new -d -s ls-py 'python3 src/py/server.py';
tmux new -d -s ls-jl 'julia --project=src/jl src/jl/server.jl';