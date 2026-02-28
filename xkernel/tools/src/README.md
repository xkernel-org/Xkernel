# Tool chains for Xkernel

There are three modules in Xkernel:

- `xkernel_build`: Generate binary diff of the kernel before and after the patch.

Usage: `./xkernel_build.sh <kernel_dir> <patch_file>`

- `xkernel_analyze`: Analyze the source code for consistency model.

- `xkernel_load`: Load/unload eBPF programs to the kernel.