#ifndef __CONSISTENCY_H__
#define __CONSISTENCY_H__

#include <linux/kernel.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>
#include <linux/list.h>
#include <linux/module.h>
#include <linux/sched.h>
#include <linux/stacktrace.h>
#include <linux/stop_machine.h>

extern struct list_head xk_target_functions;

enum xkernel_state {
  XK_FLAGS_PENDING,
  XK_FLAGS_FAILED,
  XK_FLAGS_DONE,
  XK_FLAGS_REVERSE_PENDING,
  XK_FLAGS_REVERSE_FAILED,
  XK_FLAGS_REVERSE_DONE,
};

struct xk_target_function {
#define MAX_FUNC_NAME_LEN 128
  char name[MAX_FUNC_NAME_LEN];
  /* The address of the function in the kernel */
  unsigned long address;
  /* The start offset of the function in the kernel */
  unsigned long soff;
  /* The end offset of the function in the kernel */
  unsigned long eoff;

  struct kprobe guard_kp;
  struct kprobe unguard_kp;

  bool attached_guard_kp;
  bool attached_unguard_kp;

  struct list_head list;
};

/**
 * Compare a stack address with a function span.
 * @param stack_address: The address on the stack.
 * @param function_address: The address of the function.
 * @param soff: The start offset of the function.
 * @param eoff: The end offset of the function.
 * @return: True if the stack address is within the function span, false
 * otherwise.
 */
static inline bool xk_compare_function(unsigned long stack_address,
                                       unsigned long function_address,
                                       unsigned long soff, unsigned long eoff) {
  return stack_address >= function_address + soff &&
         stack_address < function_address + eoff;
}

static int dummy_stop_machine_callback(void *data) { return 0; }

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

void xk_reset_refcount(void);
int xk_refcount(void);
void xk_inc_refcount(void);
int xk_inc_not_zero(void);
void xk_dec_refcount(void);
int xk_dec_if_positive(void);

#endif
