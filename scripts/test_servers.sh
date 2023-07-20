#!/bin/bash
echo Test Julia Language Server;
julia --project=src/jl src/jl/test/all.jl;
echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~;
echo Test Python Language Server;
python3 src/py/test/all.py;
