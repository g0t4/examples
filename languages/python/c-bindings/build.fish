#!/usr/bin/env fish

source .venv/bin/activate.fish

c++ -O3 -Wall -shared -std=c++11 -fPIC (python3 -m pybind11 --includes | string split ' ') my_module.cpp -o my_module$(python3-config --extension-suffix)

mkdir build
cmake -DPYBIND11_DIR=$(python3 -m pybind11 --cmakedir) 

