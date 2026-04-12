#ifndef __XKERNEL_H__
#define __XKERNEL_H__

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include "kfuncs.bpf.h"
#include "util.bpf.h"

char LICENSE[] SEC("license") = "GPL";

#define MEASURE_TRANSITION_TIME

/*
 * Per-task state stored in BPF task-local storage.
 *
 * epoch: matches xk_epoch at the time transition_done was set.  If the
 *        task's epoch diverges from xk_epoch (incremented by userspace when
 *        a new transition round starts), transition_done is invalidated and
 *        rechecked.  This allows multiple consecutive transitions within one
 *        BPF program lifetime.
 */
struct task_data {
    u32 transition_done;
    u32 epoch;            /* must match xk_epoch to be valid */
    u64 transition_start;
    u64 transition_end;
};

/*
 * Transition latency event emitted to the ring buffer (mode 1 only,
 * when MEASURE_TRANSITION_TIME is defined).
 */
struct transition_event {
    u64 pid_tgid;
    char comm[16];
    u64 start_ns;
    u64 end_ns;
    u64 latency_ns;
};

/*
 * Aggregate per-task transition stats (single entry, key = 0).
 * Updated atomically each time a task completes its transition.
 */
struct transition_stats {
    u64 min_ns;   /* minimum latency observed (0 = unset) */
    u64 max_ns;   /* maximum latency observed */
    u64 total_ns; /* sum of all latencies (for average) */
    u64 count;    /* number of completed per-task transitions */
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

/*
 * xk_epoch is incremented by userspace each time a new transition round
 * begins.  Per-task transition_done flags are invalidated when a task's
 * stored epoch differs from xk_epoch, enabling multiple consecutive
 * transitions in a single BPF program lifetime.
 */
SEC(".bss.xk_epoch")
u32 xk_epoch = 0;

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

#ifdef MEASURE_TRANSITION_TIME
/*
 * Ring buffer for per-task transition latency events.
 * Capacity: 64 KB — holds ~1300 events before wrapping.
 * Consumed by userspace via `xkernel-tool transition-stats`.
 */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 65536);
} transition_rb SEC(".maps");

/*
 * Aggregate stats map (single entry, key = 0).
 * Atomically updated on each per-task transition completion.
 */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct transition_stats);
} transition_stats_map SEC(".maps");
#endif /* MEASURE_TRANSITION_TIME */

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
    __u64 start;
    __u64 end;
    __u32 match_idx;
};
#define MAX_BPF_LOOP 128

static __always_inline long bs_fn(u64 index, struct bs_ctx *ctx) {
    if (!ctx) return 1;

    if (ctx->left > ctx->right) return 1;

    __u32 mid = (ctx->left + ctx->right) / 2;
    struct critical_span *cs = bpf_map_lookup_elem(&cs_map, &mid);
    if (unlikely(!cs)) return 1;
    if (ctx->addr >= cs->soff) {
        ctx->start = cs->soff;
        ctx->end = cs->eoff;
        ctx->match_idx = mid;
        ctx->found = true;
        ctx->left = mid + 1;
    } else {
        ctx->right = mid - 1;
    }

    // Continue the loop
    return 0;
}

// Binary search callback for ss_map (parallel to bs_fn for cs_map)
static __always_inline long ss_bs_fn(u64 index, struct bs_ctx *ctx) {
    if (!ctx) return 1;
    if (ctx->left > ctx->right) return 1;

    __u32 mid = (ctx->left + ctx->right) / 2;
    struct critical_span *ss = bpf_map_lookup_elem(&ss_map, &mid);
    if (unlikely(!ss)) return 1;
    if (ctx->addr >= ss->soff) {
        ctx->start = ss->soff;
        ctx->end = ss->eoff;
        ctx->match_idx = mid;
        ctx->found = true;
        ctx->left = mid + 1;
    } else {
        ctx->right = mid - 1;
    }
    return 0;
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
    __u32 len = use_ss ? ss_len : cs_len;

    stack_len = stack_size / sizeof(__u64);
    stack_len = MIN(stack_len, MAX_STACK_DEPTH);
    for (int i = 1; i < stack_len; i++) { // Skip the current function
        __u64 addr = stack[i];
        struct bs_ctx bctx = {
            .addr = addr,
            .left = 0,
            .right = len - 1,
            .found = false,
        };
        bpf_loop(MAX_BPF_LOOP, use_ss ? ss_bs_fn : bs_fn, &bctx, 0);
        if (bctx.found && bctx.end >= addr) {
            bpf_printk("[%pS] stack[%d]=%pS hit %s[%u]",
                        (void *)PT_REGS_IP(ctx), i, (void *)addr,
                        use_ss ? "ss" : "cs", bctx.match_idx);
            bpf_printk("  range [%lx, %lx]", bctx.start, bctx.end);
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

    /*
     * Epoch check: if the stored epoch is stale (userspace incremented
     * xk_epoch to start a new transition round), reset the per-task state
     * so this task re-runs the transition check.
     */
    u32 current_epoch = xk_epoch;
    if (data->epoch != current_epoch) {
        data->transition_done  = 0;
        data->transition_start = 0;
        data->transition_end   = 0;
        data->epoch            = current_epoch;
    }

    if (likely(data->transition_done)) return;

    #ifdef MEASURE_TRANSITION_TIME
    if (data->transition_start == 0)
        data->transition_start = bpf_ktime_get_ns();
    #endif
    
    data->transition_done = check_stack_safe(ctx);

    #ifdef MEASURE_TRANSITION_TIME
    if (data->transition_done && data->transition_end == 0) {
        data->transition_end = bpf_ktime_get_ns();
        u64 latency_ns = data->transition_end - data->transition_start;
        LOG_CPU("transition done [%s] at %pS, took %lld us",
                task->comm, (void *)PT_REGS_IP(ctx), latency_ns / 1000);

        /* Emit event to ring buffer */
        struct transition_event *ev =
            bpf_ringbuf_reserve(&transition_rb, sizeof(*ev), 0);
        if (ev) {
            ev->pid_tgid   = bpf_get_current_pid_tgid();
            ev->start_ns   = data->transition_start;
            ev->end_ns     = data->transition_end;
            ev->latency_ns = latency_ns;
            bpf_get_current_comm(ev->comm, sizeof(ev->comm));
            bpf_ringbuf_submit(ev, 0);
        }

        /* Update aggregate stats (key = 0) */
        u32 stats_key = 0;
        struct transition_stats *st =
            bpf_map_lookup_elem(&transition_stats_map, &stats_key);
        if (st) {
            __sync_fetch_and_add(&st->count, 1);
            __sync_fetch_and_add(&st->total_ns, latency_ns);
            /* min: use cmpxchg loop approximation via fetch-and-compare */
            u64 old_min = st->min_ns;
            if (old_min == 0 || latency_ns < old_min)
                __sync_val_compare_and_swap(&st->min_ns, old_min, latency_ns);
            u64 old_max = st->max_ns;
            if (latency_ns > old_max)
                __sync_val_compare_and_swap(&st->max_ns, old_max, latency_ns);
        }
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

/*
 * Check if the current task's transition is complete AND the ConstID is
 * still active (xk_active == 1).
 *
 * Mode 0 (Immediate): always done (xk_active set to 1 at load time).
 * Mode 1 (Per-task):  xk_active && task_storage.transition_done.
 *                     xk_active is cleared during unload to stop applying
 *                     new values before BPF programs are detached.
 * Mode 2 (Global):    xk_active BSS flag, set by userspace after the
 *                     kernel module completes the stop_machine protocol.
 *
 * Used by x_transition_done() in x_tune.h; called by X_TUNE policy bodies
 * before invoking x_set().
 */
static __always_inline bool transition_done(struct pt_regs *ctx) {
    /* Global kill-switch: if xk_active is 0, never apply new values.
     * This enables safe reverse transition for all modes. */
    if (!xk_active)
        return false;

    int mode = xk_mode;
    if (mode == 0) return true;
    if (mode == 1) {
        struct task_struct *task = bpf_get_current_task_btf();
        struct task_data *data = bpf_task_storage_get(
            &task_storage, task, NULL, 0);
        if (unlikely(!data))
            return false;
        return data->transition_done;
    }
    if (mode == 2) return true; /* xk_active already checked above */
    LOG_PANIC("Invalid consistency mode: %d", mode);
    return false;
}

/* X_TUNE context structure for user policy.
 * Wraps pt_regs and the SIE indirection function pointer. */
struct x_ctx {
    struct pt_regs *regs;
    void (*set_fn)(struct pt_regs *regs, u64 val);
};

/* Check if the value transition is complete and safe to apply new values. */
static __always_inline bool x_transition_done(struct x_ctx *x_ctx) {
    if (!x_ctx || !x_ctx->regs) return false;
    return transition_done(x_ctx->regs);
}

/* Apply the new value via the SIE indirection function. */
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