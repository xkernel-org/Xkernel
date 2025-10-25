#ifndef __CONSISTENCY_H__
#define __CONSISTENCY_H__

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/sched.h>
#include <linux/stacktrace.h>
#include <linux/list.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>
#include <linux/stop_machine.h>

extern struct list_head xk_target_functions;

enum xkernel_state {
    TRANS_PENDING,
    TRANS_FAILED,
    TRANS_DONE,
    TRANS_REVERSE_PENDING,
    TRANS_REVERSE_FAILED,
    TRANS_REVERSE_DONE,
};

struct xk_target_function {
    #define MAX_FUNC_NAME_LEN 128
    char name[MAX_FUNC_NAME_LEN];
    /* The address of the function in the kernel */
    unsigned long address;
    /* The offset of the function in the kernel */
    unsigned long offset;
    /* The size of the function in the kernel */
    unsigned long size;

    struct kprobe guard_kp;

    bool attached_guard_kp;

    struct list_head list;
};

void xk_enable_ir_kprobes(void);
void xk_disable_ir_kprobes(void);

/**
 * Compare a stack address with a function address and size.
 * @param stack_address: The address on the stack.
 * @param function_address: The address of the function.
 * @param function_size: The size of the function.
 * @return: True if the stack address is within the function address and size, false otherwise.
 */
static inline bool xk_compare_function(unsigned long stack_address, unsigned long function_address, unsigned long function_size) {
    return stack_address >= function_address && stack_address < function_address + function_size;
}

static int dummy_stop_machine_callback(void *data) {return 0;}

/**
 * Measure the overhead of stop_machine.
 * We do this by calling stop_machine 10000 times and averaging the time taken.
 */
static inline void measure_stop_machine_overhead(void) {
    #define NUM_MEASUREMENTS 10000
    ktime_t start, end;
    u64 total_time = 0;
    int i;
    for (i = 0; i < NUM_MEASUREMENTS; i++) {
        start = ktime_get();
        stop_machine(dummy_stop_machine_callback, NULL, NULL);
        end = ktime_get();
        total_time += ktime_to_us(ktime_sub(end, start));
    }
    pr_info("stop_machine overhead: %lld us\n", total_time / NUM_MEASUREMENTS);
}


#endif