#include "my_policy_1.internal.bpf.h"

X_TUNE(cubictcp_acked, "+0x22a") {
    // 1. Safety guard (mandatory)
    if (!x_transition_done(x_ctx)) return 0;
    // 2. User policy logic
    // TODO: Implement your policy logic here
    return 0;
} /* my_policy_1.bpf.c */
