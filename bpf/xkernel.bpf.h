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

#define MAX_CS 64
struct critical_span {
    __u64 soff;
    __u64 eoff;
};

// cs_map is populated by the userspace program and is sorted by the soff and eoff.
SEC(".bss.cs_len")
__u32 cs_len = 0;

// ss_map holds Safe Span ranges for transition checking (sorted by soff).
// When ss_len > 0, check_stack_safe() uses ss_map instead of cs_map.
#define MAX_SS 64
SEC(".bss.ss_len")
__u32 ss_len = 0;

SEC(".bss.xk_mode")
int xk_mode = 0;

SEC(".bss.xk_active")
int xk_active = 0;

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, MAX_CS);
    __type(key, __u32);
    __type(value, struct critical_span);
} cs_map SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, MAX_SS);
    __type(key, __u32);
    __type(value, struct critical_span);
} ss_map SEC(".maps");

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

// Binary search callback for ss_map (parallel to bs_fn for cs_map)
static __always_inline long ss_bs_fn(u64 index, struct bs_ctx *ctx) {
    if (!ctx) return 1;
    if (ctx->left > ctx->right) return 1;

    __u32 mid = (ctx->left + ctx->right) / 2;
    struct critical_span *ss = bpf_map_lookup_elem(&ss_map, &mid);
    if (unlikely(!ss)) return 1;
    if (ctx->addr >= ss->soff) {
        ctx->end = ss->eoff;
        ctx->found = true;
        ctx->left = mid + 1;
    } else {
        ctx->right = mid - 1;
    }
    return 0;
}

static __always_inline bool contains_ss_addr(__u64 addr) {
    if (unlikely(ss_len > MAX_SS)) {
        LOG_PANIC("ss_len > MAX_SS");
        return false;
    }
    struct bs_ctx ctx = {
        .addr = addr,
        .left = 0,
        .right = ss_len - 1,
        .found = false,
        .end = 0,
    };

    long ret = bpf_loop(MAX_BPF_LOOP, ss_bs_fn, &ctx, 0);
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

    // Use SS (Safe Span) for transition checking when available;
    // fall back to CS (Critical Span) if no SS data is loaded.
    bool use_ss = (ss_len > 0);

    stack_len = stack_size / sizeof(__u64);
    stack_len = MIN(stack_len, MAX_STACK_DEPTH);
    for (int i = 1; i < stack_len; i++) { // Skip the current function
        __u64 addr = stack[i];
        bool in_span = use_ss ? contains_ss_addr(addr) : contains_addr(addr);
        if (in_span) {
            bpf_printk("stack[%d] = %lx is in a safe span", i, addr);
            return false;
        }
    }

    return true;
}

static __always_inline void per_task_transition_handler(struct pt_regs *ctx) {
    struct task_struct *task;
    struct task_data *data;

    if (unlikely(cs_len == 0 && ss_len == 0)) return;

    task = bpf_get_current_task_btf();
    data = bpf_task_storage_get(&task_storage, task, NULL, BPF_LOCAL_STORAGE_GET_F_CREATE);
    if (unlikely(!data)) return;
    if (likely(data->transition_done)) return;

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
}

// Guard handler: placed at SS entry (soff).
// Per-task mode: check callstack to determine if thread is safe.
// Global mode: no-op (kernel module handles refcount via its own kprobes).
static __always_inline void ss_guard_handler(struct pt_regs *ctx) {
    if (xk_mode == 1) {
        per_task_transition_handler(ctx);
    }
}

// Unguard handler: placed at SS exit (eoff).
// Per-task mode: no-op (transition checked at entry via stack walk).
// Global mode: no-op (kernel module handles refcount via its own kprobes).
static __always_inline void ss_unguard_handler(struct pt_regs *ctx) {
    (void)ctx;
}

static __always_inline bool per_task_transition_done(struct pt_regs *ctx) {
    struct task_struct *task;
    struct task_data *data;
    
    task = bpf_get_current_task_btf();
    data = bpf_task_storage_get(&task_storage, task, NULL, BPF_LOCAL_STORAGE_GET_F_CREATE);
    if (unlikely(!data))
        return false;
    
    return data->transition_done;
}

static __always_inline bool global_transition_done(void) {
    return xk_active == 1;
}

static __always_inline bool transition_done(struct pt_regs *ctx) {
    int mode = xk_mode;
    if (mode == 0) return true;
    if (mode == 1) return per_task_transition_done(ctx);
    if (mode == 2) return global_transition_done();
    LOG_PANIC("Invalid consistency mode: %d", mode);
    return false;
}

// X_TUNE context structure for user policy
struct x_ctx {
    struct pt_regs *regs;
    void (*set_fn)(struct pt_regs *regs, u64 val);
};

// Wrapper for transition_done that takes x_ctx
static __always_inline bool x_transition_done(struct x_ctx *x_ctx) {
    if (!x_ctx || !x_ctx->regs) return false;
    return transition_done(x_ctx->regs);
}

// Helper to set value using the set_fn callback
static __always_inline void x_set(struct x_ctx *x_ctx, u64 val) {
    if (!x_ctx || !x_ctx->set_fn || !x_ctx->regs) return;
    x_ctx->set_fn(x_ctx->regs, val);
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