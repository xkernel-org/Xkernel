#ifndef __UTIL_H__
#define __UTIL_H__

#include <bpf/bpf_helpers.h>

#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

#define LOG_CPU(fmt, ...) bpf_printk("cpu: %d, " fmt, bpf_get_smp_processor_id(), ##__VA_ARGS__);

#define LOG_AX(ctx)     bpf_printk("ctx->ax: %lx, %s:%d", ctx->ax, __FILE__, __LINE__);
#define LOG_BX(ctx)     bpf_printk("ctx->bx: %lx, %s:%d", ctx->bx, __FILE__, __LINE__);
#define LOG_CX(ctx)     bpf_printk("ctx->cx: %lx, %s:%d", ctx->cx, __FILE__, __LINE__);
#define LOG_DX(ctx)     bpf_printk("ctx->dx: %lx, %s:%d", ctx->dx, __FILE__, __LINE__);
#define LOG_SI(ctx)     bpf_printk("ctx->si: %lx, %s:%d", ctx->si, __FILE__, __LINE__);
#define LOG_DI(ctx)     bpf_printk("ctx->di: %lx, %s:%d", ctx->di, __FILE__, __LINE__);
#define LOG_BP(ctx)     bpf_printk("ctx->bp: %lx, %s:%d", ctx->bp, __FILE__, __LINE__);
#define LOG_SP(ctx)     bpf_printk("ctx->sp: %lx, %s:%d", ctx->sp, __FILE__, __LINE__);
#define LOG_IP(ctx)     bpf_printk("ctx->ip: %lx, %s:%d", ctx->ip, __FILE__, __LINE__);
#define LOG_FLAGS(ctx)  bpf_printk("ctx->flags: %lx, %s:%d", ctx->flags, __FILE__, __LINE__);
#define LOG_CS(ctx)     bpf_printk("ctx->cs: %lx, %s:%d", ctx->cs, __FILE__, __LINE__);
#define LOG_SS(ctx)     bpf_printk("ctx->ss: %lx, %s:%d", ctx->ss, __FILE__, __LINE__);

#define LOG_AX_DEC(ctx)     bpf_printk("ctx->ax: %d, %s:%d", ctx->ax, __FILE__, __LINE__);
#define LOG_BX_DEC(ctx)     bpf_printk("ctx->bx: %d, %s:%d", ctx->bx, __FILE__, __LINE__);
#define LOG_CX_DEC(ctx)     bpf_printk("ctx->cx: %d, %s:%d", ctx->cx, __FILE__, __LINE__);
#define LOG_DX_DEC(ctx)     bpf_printk("ctx->dx: %d, %s:%d", ctx->dx, __FILE__, __LINE__);
#define LOG_SI_DEC(ctx)     bpf_printk("ctx->si: %d, %s:%d", ctx->si, __FILE__, __LINE__);
#define LOG_DI_DEC(ctx)     bpf_printk("ctx->di: %d, %s:%d", ctx->di, __FILE__, __LINE__);
#define LOG_BP_DEC(ctx)     bpf_printk("ctx->bp: %d, %s:%d", ctx->bp, __FILE__, __LINE__);
#define LOG_SP_DEC(ctx)     bpf_printk("ctx->sp: %d, %s:%d", ctx->sp, __FILE__, __LINE__);
#define LOG_IP_DEC(ctx)     bpf_printk("ctx->ip: %d, %s:%d", ctx->ip, __FILE__, __LINE__);
#define LOG_FLAGS_DEC(ctx)  bpf_printk("ctx->flags: %d, %s:%d", ctx->flags, __FILE__, __LINE__);
#define LOG_CS_DEC(ctx)     bpf_printk("ctx->cs: %d, %s:%d", ctx->cs, __FILE__, __LINE__);
#define LOG_SS_DEC(ctx)     bpf_printk("ctx->ss: %d, %s:%d", ctx->ss, __FILE__, __LINE__);

/**
 * @brief Dump all registers in ctx
 * 
 * @param ctx
 */
static __always_inline 
void dump_ctx(struct pt_regs *ctx) {
    LOG_AX(ctx);
    LOG_BX(ctx);
    LOG_CX(ctx);
    LOG_DX(ctx);
    LOG_SI(ctx);
    LOG_DI(ctx);
    LOG_BP(ctx);
    LOG_SP(ctx);
    LOG_IP(ctx);
    LOG_FLAGS(ctx);
    LOG_CS(ctx);
    LOG_SS(ctx);
}

/**
 * @brief Calculate the new value of eax if we want to change the old_const to new_const.
 * 
 * @param old_const
 * @param new_const
 * @param old_eax
 * @return u64
 */
static __always_inline
u64 calc_value(u64 old_const, u64 new_const, u64 old_eax)
{
    u64 new_eax;

    int diff = (int)(new_const - old_const);

    if (diff == 0)
        return old_eax;

    if (diff > 0) {
        u64 dec = MIN(diff, old_eax);
        new_eax = old_eax - dec;
    } else {
        u64 inc = -diff;
        new_eax = old_eax + inc;
    }
    return new_eax;
}

#endif