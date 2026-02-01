#include "my_policy_4.internal.bpf.h"

X_TUNE(tcp_rack_detect_loss, "+0x6e") {
    // 1. Safety guard (mandatory)
    if (!x_transition_done(x_ctx)) return 0;
    // 2. User policy logic
    // TODO: Implement your policy logic here
    return 0;
} /* my_policy_4.bpf.c */
