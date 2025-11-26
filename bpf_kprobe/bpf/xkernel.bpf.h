#ifndef __XKERNEL_H__
#define __XKERNEL_H__

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "kfuncs.bpf.h"
#include "util.bpf.h"

char LICENSE[] SEC("license") = "GPL";

#define MEASURE_TRANSITION_TIME

struct task_data {
    u32 transition_done;
    u64 transition_start;
    u64 transition_end;
};

#define MAX_CS 16
struct critical_span {
    __u64 soff;
    __u64 eoff;
};

// cs_map is populated by the userspace program and is sorted by the soff and eoff.
SEC(".bss.cs_len")
__u32 cs_len = 0;
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, MAX_CS);
    __type(key, __u32);
    __type(value, struct critical_span);
} cs_map SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_TASK_STORAGE);
    __uint(map_flags, BPF_F_NO_PREALLOC);
    __type(key, int);
    __type(value, struct task_data);          
} task_storage SEC(".maps");

#define MAX_STACK_ENTRIES 1024
#define MAX_STACK_DEPTH 32

// Binary search to match a single address
// Use binary search on the sorted range list to find the largest interval index k where start ≤ x (if none exists, x is not in any interval).
// Check if the end of interval k is ≥ x:
// If yes, x is in the interval;
// If not, because intervals are sorted by start in ascending order, all subsequent intervals have start > x, so x is not in any interval.
struct bs_ctx {
    __u64 addr;
    __u32 left;
    __u32 right;
    bool found;
    __u64 end;
};
#define MAX_BPF_LOOP 128

static __always_inline long bs_fn(u64 index, struct bs_ctx *ctx) {
    if (!ctx) return 1;

    if (ctx->left > ctx->right) return 1;

    __u32 mid = (ctx->left + ctx->right) / 2;
    struct critical_span *cs = bpf_map_lookup_elem(&cs_map, &mid);
    if (unlikely(!cs)) return 1;
    if (ctx->addr >= cs->soff) {
        ctx->end = cs->eoff;
        ctx->found = true;
        ctx->left = mid + 1;
    } else {
        ctx->right = mid - 1;
    }

    // Continue the loop
    return 0;
} 

static __always_inline bool contains_addr(__u64 addr) {
    if (unlikely(cs_len > MAX_CS)) {
        LOG_PANIC("cs_len > MAX_CS");
        return false;
    }
    struct bs_ctx ctx = {
        .addr = addr,
        .left = 0,
        .right = cs_len - 1,
        .found = false,
        .end = 0,
    };

    long ret = bpf_loop(MAX_BPF_LOOP, bs_fn, &ctx, 0);
    if (unlikely(ret < 0)) {
        LOG_PANIC("bpf_loop failed");
        return false;
    }
    if (!ctx.found) return false;

    return ctx.end >= addr;
}

static __always_inline bool check_stack_safe(struct pt_regs *ctx) {
    __u64 stack[MAX_STACK_DEPTH];
    __u32 stack_size, stack_len;
    stack_size = bpf_get_stack(ctx, stack, MAX_STACK_DEPTH, 0);
    if (stack_size <= 0) {
        bpf_printk("Failed to get stack: %d", stack_size);
        return false;
    }

    stack_len = stack_size / sizeof(__u64);
    stack_len = MIN(stack_len, MAX_STACK_DEPTH);
    for (int i = 0; i < stack_len; i++) {
        __u64 addr = stack[i];
        if (contains_addr(addr)) {
            bpf_printk("stack[%d] = %lx is in a critical span", i, addr);
            return false;
        }
    }

    return true;
}

static __always_inline bool per_task_transition_done(struct pt_regs *ctx) {
    struct task_struct *task;
    struct task_data *data;

    if (unlikely(cs_len == 0))
        return false;

    
    task = bpf_get_current_task_btf();
    data = bpf_task_storage_get(&task_storage, task, NULL, BPF_LOCAL_STORAGE_GET_F_CREATE);
    if (unlikely(!data))
        return false;
    if (likely(data->transition_done))
        return true;

    #ifdef MEASURE_TRANSITION_TIME
    if (data->transition_start == 0)
        data->transition_start = bpf_ktime_get_ns();
    #endif
    
    data->transition_done = check_stack_safe(ctx);

    #ifdef MEASURE_TRANSITION_TIME
    if (data->transition_done && data->transition_end == 0) {
        data->transition_end = bpf_ktime_get_ns();
        u64 check_time = data->transition_end - data->transition_start;
        LOG_CPU("task: [%s], ktime_ns: %lld, check time: %lld us", task->comm, data->transition_end, check_time / 1000);
    }
    #endif
    
    return data->transition_done;
}

static __always_inline bool global_transition_done(void) {
    return kfuncs_is_ir_kprobes_on();
}

static __always_inline bool transition_done(struct pt_regs *ctx) {
    int mode = kfuncs_get_consistency_mode();
    if (mode == 0) return true;
    if (mode == 1) return per_task_transition_done(ctx);
    if (mode == 2) return global_transition_done();
    LOG_PANIC("Invalid consistency mode: %d", mode);
    return false;
}

#define BPF_ONESHOT_INIT(name) \
    SEC("syscall") \
    int oneshot_init_##name(void *ctx) \

#define BPF_ONESHOT_EXIT(name) \
    SEC("syscall") \
    int oneshot_exit_##name(void *ctx) \

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