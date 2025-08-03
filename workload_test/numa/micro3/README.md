AI generated

Each thread accessing its own private data. The following can be observed

- Turning on/off `kernel.numa_balancing` won't cause much difference
- Wrapped by cgroup, pinning memory to one node first and then lifting this
  constrain, `kernel.numa_balancing` makes a difference.
- No observable effect from `NUMA_PERIOD_THRESHOLD` yet
