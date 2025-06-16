#ifndef __UTIL_H__
#define __UTIL_H__

#include <bpf/bpf_helpers.h>

#include "kfuncs.bpf.h"

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

#define BPF_AX(ctx) ((u64)(ctx->ax))
#define BPF_BX(ctx) ((u64)(ctx->bx))
#define BPF_CX(ctx) ((u64)(ctx->cx))
#define BPF_DX(ctx) ((u64)(ctx->dx))
#define BPF_SI(ctx) ((u64)(ctx->si))
#define BPF_DI(ctx) ((u64)(ctx->di))
#define BPF_BP(ctx) ((u64)(ctx->bp))
#define BPF_SP(ctx) ((u64)(ctx->sp))
#define BPF_IP(ctx) ((u64)(ctx->ip))
#define BPF_FLAGS(ctx) ((u64)(ctx->flags))
#define BPF_CS(ctx) ((u64)(ctx->cs))
#define BPF_SS(ctx) ((u64)(ctx->ss))

#define BPF_32BIT_MASK 0xffffffff
#define BPF_EAX(ctx) ((u64)(ctx->ax) & BPF_32BIT_MASK)
#define BPF_EBX(ctx) ((u64)(ctx->bx) & BPF_32BIT_MASK)
#define BPF_ECX(ctx) ((u64)(ctx->cx) & BPF_32BIT_MASK)
#define BPF_EDX(ctx) ((u64)(ctx->dx) & BPF_32BIT_MASK)
#define BPF_ESI(ctx) ((u64)(ctx->si) & BPF_32BIT_MASK)
#define BPF_EDI(ctx) ((u64)(ctx->di) & BPF_32BIT_MASK)
#define BPF_EBP(ctx) ((u64)(ctx->bp) & BPF_32BIT_MASK)
#define BPF_ESP(ctx) ((u64)(ctx->sp) & BPF_32BIT_MASK)
#define BPF_EIP(ctx) ((u64)(ctx->ip) & BPF_32BIT_MASK)
#define BPF_EFLAGS(ctx) ((u64)(ctx->flags) & BPF_32BIT_MASK)
#define BPF_ECS(ctx) ((u64)(ctx->cs) & BPF_32BIT_MASK)
#define BPF_ESS(ctx) ((u64)(ctx->ss) & BPF_32BIT_MASK)

#define BPF_SET_EAX(ctx, value) \
    do { \
        u64 eax = (value) & BPF_32BIT_MASK; \
        kfuncs_probe_write_kernel(&ctx->ax, sizeof(eax), &eax, sizeof(eax)); \
    } while (0)

#define BPF_SET_EBX(ctx, value) \
    do { \
        u64 ebx = (value) & BPF_32BIT_MASK; \
        kfuncs_probe_write_kernel(&ctx->bx, sizeof(ebx), &ebx, sizeof(ebx)); \
    } while (0)

#define BPF_SET_ECX(ctx, value) \
    do { \
        u64 ecx = (value) & BPF_32BIT_MASK; \
        kfuncs_probe_write_kernel(&ctx->cx, sizeof(ecx), &ecx, sizeof(ecx)); \
    } while (0)

// https://en.wikipedia.org/wiki/FLAGS_register

#define BPF_ZF_MASK 0x0040
#define BPF_SF_MASK 0x0080
#define BPF_OF_MASK 0x0800

#define BPF_ZF(ctx) ((u64)(ctx->flags) & BPF_ZF_MASK)
#define BPF_SF(ctx) ((u64)(ctx->flags) & BPF_SF_MASK)
#define BPF_OF(ctx) ((u64)(ctx->flags) & BPF_OF_MASK)

// ZF = 0 and SF = OF
#define BPF_JG(ctx) (BPF_ZF(ctx) == 0 && BPF_SF(ctx) == BPF_OF(ctx))
// Set  to make JG true
#define BPF_SET_JG_TRUE(ctx) \
    do { \
        u64 flags = BPF_EFLAGS(ctx); \
        flags &= ~BPF_ZF_MASK; \
        flags &= ~BPF_SF_MASK; \
        flags &= ~BPF_OF_MASK; \
        kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags, sizeof(flags)); \
    } while (0)

// Set ZF = 1 to make JG false
#define BPF_SET_JG_FALSE(ctx) \
    do { \
        u64 flags = BPF_EFLAGS(ctx); \
        flags |= BPF_ZF_MASK; \
        kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags, sizeof(flags)); \
    } while (0)

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

#endif