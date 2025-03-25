# 
# ! REMEMBER package IMPORTS are relative to the workspace root
#   in the case of a venv, the dir its created in 
#   launch python/nvim/ipython all from the root dir
#   DO NOT OPEN neovim in a nested dir, otherwise package imports will fail
#
from helpers.trees import *
import torch
import numpy as np

#%% 1D

array1D = np.random.rand(4)
print(array1D)
print_tree(array1D)
print_treearrays(array1D)

#%% 2D 

array2D = np.random.rand(2, 2)

print(array2D)
print_tree(array2D)
print_treearrays(array2D)

#%% 3D 

array3D = np.random.rand(2, 3, 2)

print(array3D)
print_tree(array3D)
print_treearrays(array3D)

#%% 3D smaller

# increasingly obvious to me that tree makes more sense at 3D+
#   yes, numpy compact array structure is similar and saves screen space but it is easy to lose track of the [] and thus lose track of the dimensions
array3Dsmaller = np.random.rand(2, 1, 1)
print(array3Dsmaller)
print_tree(array3Dsmaller)
print_treearrays(array3Dsmaller)

#%% works w/ torch too

tensor = torch.rand(5, 3)
print(tensor)
print_tree(tensor)
print_treearrays(tensor)
