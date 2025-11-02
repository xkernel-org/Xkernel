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
MODULE_AUTHOR("Zhongjie, Wentao");
MODULE_DESCRIPTION("A kernel module for loading kfuncs into kernel");

bool ir_kprobes_on = false;
EXPORT_SYMBOL(ir_kprobes_on);

// 0: global consistency model
// 1: per-task consistency model
int kMode = 2;
module_param(kMode, int, 0644);
MODULE_PARM_DESC(kMode, "0: Immediate, 1: Per-task, 2: Global");
EXPORT_SYMBOL(kMode);

// Per-task consistency model
// 0: all tasks are not ready
// 1: traverse pid list to check if ready
// 2: all tasks are ready
int transition = 0;
EXPORT_SYMBOL(transition);
struct transition_task {
  pid_t pid;
  struct hlist_node node;
};
// This list is protected by RCU and shared with consistency kernel module.
#define TRANSITION_TASK_HASH_BITS 8
DEFINE_HASHTABLE(transition_task_hash_table, TRANSITION_TASK_HASH_BITS);
EXPORT_SYMBOL(transition_task_hash_table);

static bool check_transition_done(pid_t pid) {
  struct transition_task *task;
  int bucket = hash_32(pid, TRANSITION_TASK_HASH_BITS);
  rcu_read_lock();
  hlist_for_each_entry_rcu(task, &transition_task_hash_table[bucket], node) {
    if (task->pid == pid) {
      rcu_read_unlock();
      return false;
    }
  }
  rcu_read_unlock();
  return true;
}

__bpf_kfunc_start_defs();
__bpf_kfunc bool kfuncs_is_ir_kprobes_on(void) {
  if (kMode == 0) { // Immediate
    return true;
  } else if (kMode == 1) { // Per-task consistency model
    int t = READ_ONCE(transition);
    if (t == 0) {
      return false;
    } else if (t == 2) {
      return true;
    } else {
      return check_transition_done(current->pid);
    }
  } else { // Global consistency model
    return READ_ONCE(ir_kprobes_on);
  }
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
#define MAX_INSN_SIZE 8
__bpf_kfunc int kfuncs_text_poke(void *addr__ign, void *insn__ign, __u32 insn_len__sz) {
  if (insn_len__sz > MAX_INSN_SIZE)
  return -EINVAL;
#ifdef BPF_TEXT_POKE
  (void)text_poke(addr__ign, insn__ign, insn_len__sz);
#endif
  return 0;
}
__bpf_kfunc_end_defs();

#if LINUX_VERSION_CODE <= KERNEL_VERSION(6, 9, 0)
BTF_SET8_START(bpf_kfunc_example_ids_set)
BTF_ID_FLAGS(func, kfuncs_probe_write_kernel)
BTF_ID_FLAGS(func, kfuncs_is_ir_kprobes_on)
  #ifdef BPF_TEXT_POKE
  BTF_ID_FLAGS(func, kfuncs_text_poke)
  #endif
BTF_SET8_END(bpf_kfunc_example_ids_set)
#else
BTF_KFUNCS_START(bpf_kfunc_example_ids_set)
BTF_ID_FLAGS(func, kfuncs_probe_write_kernel)
BTF_ID_FLAGS(func, kfuncs_is_ir_kprobes_on)
  #ifdef BPF_TEXT_POKE
  BTF_ID_FLAGS(func, kfuncs_text_poke)
  #endif
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
