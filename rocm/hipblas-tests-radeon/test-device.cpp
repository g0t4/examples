#include <iostream>
#include <hip/hip_runtime.h>

int main() {
    int device_id;
    hipDeviceProp_t device_prop;

    // Get the current device ID
    hipGetDevice(&device_id);

    // Get device properties
    hipGetDeviceProperties(&device_prop, device_id);

    // Print device information
    std::cout << "Using Device ID: " << device_id << std::endl;
    std::cout << "Device Name: " << device_prop.name << std::endl;
    std::cout << "Compute Capability: " << device_prop.major << "." << device_prop.minor << std::endl;
    std::cout << "Total Global Memory: " << device_prop.totalGlobalMem / (1024 * 1024) << " MB" << std::endl;
    std::cout << "Multiprocessors: " << device_prop.multiProcessorCount << std::endl;
    std::cout << "Max Threads per Block: " << device_prop.maxThreadsPerBlock << std::endl;

    return 0;
}

