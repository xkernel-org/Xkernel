/**
    // sudo bpftool prog load ./bpf_prog.o /sys/fs/bpf/my_kprobe
    // sudo bpftool prog show
    // sudo rm -rf /sys/fs/bpf/my_kprobe

    sudo echo 'p:my_kprobe 0xffffffff817cb288' | sudo tee /sys/kernel/debug/tracing/kprobe_events
    sudo echo 1 | sudo tee /sys/kernel/debug/tracing/events/kprobes/my_kprobe/enable

    sudo echo 0 | sudo tee /sys/kernel/debug/tracing/events/kprobes/my_kprobe/enable
    sudo echo '-:my_kprobe' | sudo tee /sys/kernel/debug/tracing/kprobe_events

    sudo cat /sys/kernel/debug/tracing/trace_pipe
 */
#include <linux/types.h>
#include <linux/ptrace.h>
#include <linux/bpf.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>

struct request {
    unsigned long cmd_flags;
};

int print_req(unsigned long reg) {
    struct request *req = (struct request *)reg;
    unsigned long cmd_flags = BPF_CORE_READ(req, cmd_flags);
    bpf_printk("req->cmd_flags: %lx\n", cmd_flags);
    return 0;
}

SEC("kprobe/0xffffffff817cb288")
int blk_test(struct pt_regs *ctx) {
    unsigned long req = PT_REGS_PARM1(ctx);
    return print_req(req);
}

// Test for openat
// SEC("kprobe/__x64_sys_openat")
// int do_sys_openat(struct pt_regs *ctx) {
//     bpf_printk("__x64_sys_openat called\\n");
//     return 0;
// }

char _license[] SEC("license") = "GPL";