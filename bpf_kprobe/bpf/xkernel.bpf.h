#ifndef __XKERNEL_H__
#define __XKERNEL_H__

#include "kfuncs.bpf.h"
#include "util.bpf.h"

char LICENSE[] SEC("license") = "GPL";

#define BPF_ONESHOT_INIT(name) \
    SEC("syscall") \
    int oneshot_init_##name(void *ctx) \

#define BPF_ONESHOT_EXIT(name) \
    SEC("syscall") \
    int oneshot_exit_##name(void *ctx) \

#define MAX_STACK_ENTRIES 1024
#define MAX_STACK_DEPTH 127

// <stack_id, count>
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_STACK_ENTRIES);
    __type(key, u32);
    __type(value, u64);
} stack_count_map SEC(".maps");

// <stack_id, stack_trace>
struct {
    __uint(type, BPF_MAP_TYPE_STACK_TRACE);
    __uint(max_entries, MAX_STACK_ENTRIES);
    __type(key, u32);
    __type(value, u64[MAX_STACK_DEPTH]);
} stack_trace_map SEC(".maps");

SEC(".bss.call_store_stack")
u32 call_store_stack_id = 0;

// Gemini told me that bpf_get_stackid is thread-safe.
static __always_inline int store_call_stack(struct pt_regs *ctx) {
    
    call_store_stack_id = 1;
    
    s32 stack_id = bpf_get_stackid(ctx, &stack_trace_map, 0);
    if (stack_id < 0) {
        bpf_printk("Failed to get stack id: %d", stack_id);
        return -1;
    }

    u64 *stack_count = bpf_map_lookup_elem(&stack_count_map, &stack_id);
    if (!stack_count) {
        u64 initial_count = 1;
        bpf_map_update_elem(&stack_count_map, &stack_id, &initial_count, BPF_ANY);
    } else {
        __sync_fetch_and_add(stack_count, 1);
    }
    return 0;
}
    
#endif