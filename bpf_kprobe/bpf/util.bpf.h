#ifndef __UTIL_H__
#define __UTIL_H__

#include <bpf/bpf_helpers.h>

/**
 * @brief Dump all registers in ctx
 * 
 * @param ctx
 */
static __always_inline 
void dump_ctx(struct pt_regs *ctx) {
    bpf_printk("current ctx->ax: %lx", ctx->ax);
    bpf_printk("current ctx->bx: %lx", ctx->bx);
    bpf_printk("current ctx->cx: %lx", ctx->cx);
    bpf_printk("current ctx->dx: %lx", ctx->dx);
    bpf_printk("current ctx->si: %lx", ctx->si);
    bpf_printk("current ctx->di: %lx", ctx->di);
    bpf_printk("current ctx->bp: %lx", ctx->bp);
    bpf_printk("current ctx->sp: %lx", ctx->sp);
    bpf_printk("current ctx->ip: %lx", ctx->ip);
    bpf_printk("current ctx->flags: %lx", ctx->flags);
    bpf_printk("current ctx->cs: %lx", ctx->cs);
    bpf_printk("current ctx->ss: %lx", ctx->ss);
}

#endif