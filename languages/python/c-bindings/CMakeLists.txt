cmake_minimum_required(VERSION 3.12)
project(my_project)

find_package(pybind11 REQUIRED)  # Find Pybind11 package

# Create a Python extension module named 'my_module'
pybind11_add_module(my_module my_module.cpp)
