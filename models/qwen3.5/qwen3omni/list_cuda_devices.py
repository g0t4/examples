import torch

def list_cuda_devices():
    """Print a summary of all CUDA devices visible to torch."""

    if not torch.cuda.is_available():
        print("CUDA is not available on this system.")
        return

    device_count = torch.cuda.device_count()
    current_idx = torch.cuda.current_device()

    for idx in range(device_count):
        name = torch.cuda.get_device_name(idx)
        print(f"{idx:>3}  {name:<30}")

        # props = torch.cuda.get_device_properties(idx)

        capability = torch.cuda.get_device_capability(idx)  # (major, minor)
        print(f"{'':>3}  {'Capability:':<30}  {capability[0]}.{capability[1]}")

        memory_info = torch.cuda.memory.mem_get_info(idx)
        free_memory_mib = memory_info[0] / (1024**2)
        total_memory_mib = memory_info[1] / (1024**2)
        used_memory_mib = total_memory_mib - free_memory_mib
        print(f"{'':>3}  {'Used Memory (MiB):':<30}  {used_memory_mib:16,.2f}")
        print(f"{'':>3}  {'Free Memory (MiB):':<30}  {free_memory_mib:16,.2f}")
        print(f"{'':>3}  {'Total Memory (MiB):':<30}  {total_memory_mib:16,.2f}")

        active = "←" if idx == current_idx else ""
        print(f"{'':>3}  {'Active:':<30}  {active:>6}")

list_cuda_devices()
