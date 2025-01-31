#!/usr/bin/env fish

set PATH /opt/rocm/bin $PATH

hipcc  -lhipblas test-device.cpp -o test-device
hipcc  -lhipblas test-matrix.cpp -o test-matrix
