#include <linux/bpf.h>
#include <linux/btf.h>
#include <linux/btf_ids.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/version.h>
#include <asm/text-patching.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Zhongjie");
MODULE_DESCRIPTION("A kernel module for loading kfuncs into kernel");

__bpf_kfunc_start_defs();
__bpf_kfunc long kfuncs_probe_write_kernel(void *dst__ign, __u32 dst__sz,
                                          const void *src__ign, __u32 src__sz) {
  __u32 copy_size = min(dst__sz, src__sz);
  return copy_to_kernel_nofault(dst__ign, src__ign, copy_size);
}
#define MAX_INSN_SIZE 8
__bpf_kfunc int kfuncs_text_poke(void *addr__ign, void *insn__ign, __u32 insn_len__sz) {
  if (insn_len__sz > MAX_INSN_SIZE)
    return -EINVAL;
  (void)text_poke(addr__ign, insn__ign, insn_len__sz);
  return 0;
}
__bpf_kfunc_end_defs();

#if LINUX_VERSION_CODE <= KERNEL_VERSION(6, 9, 0)
BTF_SET8_START(bpf_kfunc_example_ids_set)
BTF_ID_FLAGS(func, kfuncs_probe_write_kernel)
BTF_ID_FLAGS(func, kfuncs_text_poke)
BTF_SET8_END(bpf_kfunc_example_ids_set)
#else
BTF_KFUNCS_START(bpf_kfunc_example_ids_set)
BTF_ID_FLAGS(func, kfuncs_probe_write_kernel)
BTF_ID_FLAGS(func, kfuncs_text_poke)
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
