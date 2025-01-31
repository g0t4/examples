#include <iostream>
#include <hip/hip_runtime.h>
#include <hipblas/hipblas.h>

void checkHipError(hipError_t err) {
    if (err != hipSuccess) {
        std::cerr << "HIP Error: " << hipGetErrorString(err) << std::endl;
        exit(EXIT_FAILURE);
    }
}

void checkHipblasError(hipblasStatus_t status) {
    if (status != HIPBLAS_STATUS_SUCCESS) {
        std::cerr << "HIPBLAS Error: " << status << std::endl;
        exit(EXIT_FAILURE);
    }
}

int main() {
    // Define matrix (3x3) and vector (3x1)
    const int N = 3;
    float h_A[N * N] = {1, 2, 3, 4, 5, 6, 7, 8, 9};
    float h_x[N] = {1, 1, 1};
    float h_y[N] = {0, 0, 0};

    // Allocate device memory
    float *d_A, *d_x, *d_y;
    checkHipError(hipMalloc(&d_A, N * N * sizeof(float)));
    checkHipError(hipMalloc(&d_x, N * sizeof(float)));
    checkHipError(hipMalloc(&d_y, N * sizeof(float)));

    // Copy data to device
    checkHipError(hipMemcpy(d_A, h_A, N * N * sizeof(float), hipMemcpyHostToDevice));
    checkHipError(hipMemcpy(d_x, h_x, N * sizeof(float), hipMemcpyHostToDevice));

    // Create handle
    hipblasHandle_t handle;
    checkHipblasError(hipblasCreate(&handle));

    // Perform matrix-vector multiplication: y = A * x
    float alpha = 1.0f, beta = 0.0f;
    checkHipblasError(hipblasSgemv(handle, HIPBLAS_OP_N, N, N, &alpha, d_A, N, d_x, 1, &beta, d_y, 1));

    // Copy result back to host
    checkHipError(hipMemcpy(h_y, d_y, N * sizeof(float), hipMemcpyDeviceToHost));

    // Print result
    std::cout << "Result (y = A * x):\n";
    for (int i = 0; i < N; i++)
        std::cout << h_y[i] << " ";
    std::cout << std::endl;

    // Cleanup
    hipblasDestroy(handle);
    hipFree(d_A);
    hipFree(d_x);
    hipFree(d_y);

    return 0;
}

