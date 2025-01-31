# AMD GPU support
sudo pacman --needed --noconfirm -S \
    rocm-hip-sdk rocminfo rocm-hip-runtime hipblas

# not in path
/opt/rocm/bin/rocminfo
# not sure I want this in path for good?
#

# ggml =>
z ggml
source .venv/bin/activate.fish
set PATH /opt/rocm/bin $PATH
cmake -DCMAKE_C_COMPILER="$(hipconfig -l)/clang" -DCMAKE_CXX_COMPILER="$(hipconfig -l)/clang++" -DGGML_HIP=ON

# activate hipcc "env"
set PATH /opt/rocm/bin $PATH
set LD_LIBRARY_PATH /opt/rocm/lib $LD_LIBRARY_PATH
export LD_LIBRARY_PATH
set CPATH /opt/rocm/include $CPATH
export CPATH
