#include <linux/bpf.h>
#include <linux/btf.h>
#include <linux/btf_ids.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/version.h>
#include <linux/hashtable.h>
#include <asm/text-patching.h>

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("A kernel module for loading kfuncs into kernel");

bool ir_kprobes_on = false;
EXPORT_SYMBOL(ir_kprobes_on);

// 0: global consistency model
// 1: per-task consistency model
int kMode = 2;
module_param(kMode, int, 0644);
MODULE_PARM_DESC(kMode, "0: Immediate, 1: Per-task, 2: Global");
EXPORT_SYMBOL(kMode);

__bpf_kfunc_start_defs();
__bpf_kfunc int kfuncs_get_consistency_mode(void) {
  return kMode;
}
__bpf_kfunc bool kfuncs_is_ir_kprobes_on(void) {
  return READ_ONCE(ir_kprobes_on);
}
__bpf_kfunc_end_defs();

__bpf_kfunc_start_defs();
__bpf_kfunc long kfuncs_probe_write_kernel(void *dst__ign, __u32 dst__sz,
                                          const void *src__ign, __u32 src__sz) {
  __u32 copy_size = min(dst__sz, src__sz);
  #if LINUX_VERSION_CODE <= KERNEL_VERSION(6, 12, 0)
  memcpy(dst__ign, src__ign, copy_size);
  return 0;
  #else
  return copy_to_kernel_nofault(dst__ign, src__ign, copy_size);
  #endif
}
__bpf_kfunc_end_defs();

#if LINUX_VERSION_CODE <= KERNEL_VERSION(6, 9, 0)
BTF_SET8_START(bpf_kfunc_example_ids_set)
BTF_ID_FLAGS(func, kfuncs_probe_write_kernel)
BTF_ID_FLAGS(func, kfuncs_is_ir_kprobes_on)
BTF_ID_FLAGS(func, kfuncs_get_consistency_mode)
BTF_SET8_END(bpf_kfunc_example_ids_set)
#else
BTF_KFUNCS_START(bpf_kfunc_example_ids_set)
BTF_ID_FLAGS(func, kfuncs_probe_write_kernel)
BTF_ID_FLAGS(func, kfuncs_is_ir_kprobes_on)
BTF_ID_FLAGS(func, kfuncs_get_consistency_mode)
BTF_KFUNCS_END(bpf_kfunc_example_ids_set)
#endif

static const struct btf_kfunc_id_set bpf_kfunc_set = {
    .owner = THIS_MODULE,
    .set = &bpf_kfunc_example_ids_set,
};

static int __init kfuncs_init(void) {
  int ret;

  ret = register_btf_kfunc_id_set(BPF_PROG_TYPE_UNSPEC, &bpf_kfunc_set);
  if (ret < 0) {
    pr_err("Failed to register kfunc: %d\n", ret);
    return ret;
  }

  pr_info("kfuncs module loaded\n");
  return 0;
}

static void __exit kfuncs_exit(void) { pr_info("kfuncs module unloaded\n"); }

module_init(kfuncs_init);
module_exit(kfuncs_exit);
