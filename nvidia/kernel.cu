extern "C" __global__ void add(int *out, const int *a, const int *b) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    out[i] = a[i] + b[i];
}
