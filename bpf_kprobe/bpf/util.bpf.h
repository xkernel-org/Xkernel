#ifndef __UTIL_H__
#define __UTIL_H__

#include <bpf/bpf_helpers.h>

#include "kfuncs.bpf.h"

#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

#define ONE_SHOT_ENV(addr, len) \
  SEC(".bss"); \
  void *__target_addr = (void *)addr; \
  bool __old_insn_valid = false; \
  unsigned char __old_insn[len] = {}; \
  unsigned char __insn[len] = {};

#define BPF_READ_OLD_INSN() \
  bpf_probe_read_kernel(__old_insn, sizeof(__old_insn), __target_addr); \
  __old_insn_valid = true; \

#define BPF_READ_INSN() \
  bpf_probe_read_kernel(__insn, sizeof(__insn), __target_addr); \

#define BPF_WRITE_INSN(new_insn) \
  do { \
    if (sizeof(new_insn) == sizeof(__insn)) { \
      /* read old insn first */ \
      BPF_READ_OLD_INSN(); \
      /* write new insn */ \
      kfuncs_text_poke(__target_addr, new_insn, sizeof(new_insn)); \
    } \
  } while (0) \

#define BPF_RESTORE_INSN() \
  do { \
  if (__old_insn_valid) { \
    /* restore old insn */ \
    kfuncs_text_poke(__target_addr, __old_insn, sizeof(__old_insn)); \
  } \
  } while (0)

#define BPF_PRINT_INSN(info) \
  do { \
  BPF_READ_INSN(); \
  switch (sizeof(__insn)) { \
    case 2: LOG_INSN_2(__insn, info); break; \
    case 3: LOG_INSN_3(__insn, info); break; \
    case 4: LOG_INSN_4(__insn, info); break; \
    case 5: LOG_INSN_5(__insn, info); break; \
    case 6: LOG_INSN_6(__insn, info); break; \
    case 7: LOG_INSN_7(__insn, info); break; \
    case 8: LOG_INSN_8(__insn, info); break; \
    default: bpf_printk("unknown insn size: %d", sizeof(__insn)); break; \
  } \
  } while (0)

#define LOG_INSN_2(insn, info) \
  bpf_printk("[%s]insn: %02x %02x", info, \
    (unsigned char)insn[0], \
    (unsigned char)insn[1]);

#define LOG_INSN_3(insn, info) \
  bpf_printk("[%s]insn: %02x %02x %02x", info, \
    (unsigned char)insn[0], \
    (unsigned char)insn[1], \
    (unsigned char)insn[2]);

#define LOG_INSN_4(insn, info) \
  bpf_printk("[%s]insn: %02x %02x %02x %02x", info, \
    (unsigned char)insn[0], \
    (unsigned char)insn[1], \
    (unsigned char)insn[2], \
    (unsigned char)insn[3]);

#define LOG_INSN_5(insn, info) \
  bpf_printk("[%s]insn: %02x %02x %02x %02x %02x", info, \
    (unsigned char)insn[0], \
    (unsigned char)insn[1], \
    (unsigned char)insn[2], \
    (unsigned char)insn[3], \
    (unsigned char)insn[4]);

#define LOG_INSN_6(insn, info) \
  bpf_printk("[%s]insn: %02x %02x %02x %02x %02x %02x", info, \
    (unsigned char)insn[0], \
    (unsigned char)insn[1], \
    (unsigned char)insn[2], \
    (unsigned char)insn[3], \
    (unsigned char)insn[4], \
    (unsigned char)insn[5]);

#define LOG_INSN_7(insn, info) \
  bpf_printk("[%s]insn: %02x %02x %02x %02x %02x %02x %02x", info, \
    (unsigned char)insn[0], \
    (unsigned char)insn[1], \
    (unsigned char)insn[2], \
    (unsigned char)insn[3], \
    (unsigned char)insn[4], \
    (unsigned char)insn[5], \
    (unsigned char)insn[6]);

#define LOG_INSN_8(insn, info) \
  bpf_printk("[%s]insn: %02x %02x %02x %02x %02x %02x %02x %02x", info, \
    (unsigned char)insn[0], \
    (unsigned char)insn[1], \
    (unsigned char)insn[2], \
    (unsigned char)insn[3], \
    (unsigned char)insn[4], \
    (unsigned char)insn[5], \
    (unsigned char)insn[6], \
    (unsigned char)insn[7]);

#define LOG_CPU(fmt, ...)                                                      \
  bpf_printk("cpu: %d, " fmt, bpf_get_smp_processor_id(), ##__VA_ARGS__);

#define LOG_REG(ctx, reg)                                                      \
  bpf_printk("ctx->%s: %lx, %s:%d", #reg, ctx->reg, __FILE__, __LINE__);

#define LOG_REG_DEC(ctx, reg)                                                  \
  bpf_printk("ctx->%s: %d, %s:%d", #reg, ctx->reg, __FILE__, __LINE__);

#define LOG_AX(ctx) LOG_REG(ctx, ax)
#define LOG_BX(ctx) LOG_REG(ctx, bx)
#define LOG_CX(ctx) LOG_REG(ctx, cx)
#define LOG_DX(ctx) LOG_REG(ctx, dx)
#define LOG_SI(ctx) LOG_REG(ctx, si)
#define LOG_DI(ctx) LOG_REG(ctx, di)
#define LOG_BP(ctx) LOG_REG(ctx, bp)
#define LOG_SP(ctx) LOG_REG(ctx, sp)
#define LOG_IP(ctx) LOG_REG(ctx, ip)
#define LOG_FLAGS(ctx) LOG_REG(ctx, flags)
#define LOG_CS(ctx) LOG_REG(ctx, cs)
#define LOG_SS(ctx) LOG_REG(ctx, ss)

#define LOG_AX_DEC(ctx) LOG_REG_DEC(ctx, ax)
#define LOG_BX_DEC(ctx) LOG_REG_DEC(ctx, bx)
#define LOG_CX_DEC(ctx) LOG_REG_DEC(ctx, cx)
#define LOG_DX_DEC(ctx) LOG_REG_DEC(ctx, dx)
#define LOG_SI_DEC(ctx) LOG_REG_DEC(ctx, si)
#define LOG_DI_DEC(ctx) LOG_REG_DEC(ctx, di)
#define LOG_BP_DEC(ctx) LOG_REG_DEC(ctx, bp)
#define LOG_SP_DEC(ctx) LOG_REG_DEC(ctx, sp)
#define LOG_IP_DEC(ctx) LOG_REG_DEC(ctx, ip)
#define LOG_FLAGS_DEC(ctx) LOG_REG_DEC(ctx, flags)
#define LOG_CS_DEC(ctx) LOG_REG_DEC(ctx, cs)
#define LOG_SS_DEC(ctx) LOG_REG_DEC(ctx, ss)

#define BPF_SET_REG_64(ctx, reg, value)                                        \
  do {                                                                         \
    u64 reg_value = (value);                                                   \
    kfuncs_probe_write_kernel(&ctx->reg, sizeof(reg_value), &reg_value,        \
                              sizeof(reg_value));                              \
  } while (0)

#define BPF_32BIT_MASK 0xffffffff
#define BPF_SET_REG_32(ctx, reg, value)                                        \
  do {                                                                         \
    u64 reg_value;                                                             \
    bpf_probe_read_kernel(&reg_value, sizeof(reg_value), &ctx->reg);           \
    reg_value &= 0xffffffff00000000;                                           \
    reg_value |= (value & BPF_32BIT_MASK);                                     \
    kfuncs_probe_write_kernel(&ctx->reg, sizeof(reg_value), &reg_value,        \
                              sizeof(reg_value));                              \
  } while (0)

#define BPF_16BIT_MASK 0x0000ffff
#define BPF_SET_REG_16(ctx, reg, value)                                        \
  do {                                                                         \
    u64 reg_value;                                                             \
    bpf_probe_read_kernel(&reg_value, sizeof(reg_value), &ctx->reg);           \
    reg_value &= 0xffffffffffff0000;                                           \
    reg_value |= (value & BPF_16BIT_MASK);                                     \
    kfuncs_probe_write_kernel(&ctx->reg, sizeof(reg_value), &reg_value,        \
                              sizeof(reg_value));                              \
  } while (0)

// 64-bit registers
#define BPF_RAX(ctx) ((u64)(ctx->ax))
#define BPF_RBX(ctx) ((u64)(ctx->bx))
#define BPF_RCX(ctx) ((u64)(ctx->cx))
#define BPF_RDX(ctx) ((u64)(ctx->dx))
#define BPF_RSI(ctx) ((u64)(ctx->si))
#define BPF_RDI(ctx) ((u64)(ctx->di))
#define BPF_RBP(ctx) ((u64)(ctx->bp))
#define BPF_RSP(ctx) ((u64)(ctx->sp))
#define BPF_RIP(ctx) ((u64)(ctx->ip))
#define BPF_RFLAGS(ctx) ((u64)(ctx->flags))
#define BPF_RCS(ctx) ((u64)(ctx->cs))
#define BPF_RSS(ctx) ((u64)(ctx->ss))

#define BPF_R12(ctx) ((u64)(ctx->r12))
#define BPF_R13(ctx) ((u64)(ctx->r13))
#define BPF_R14(ctx) ((u64)(ctx->r14))
#define BPF_R15(ctx) ((u64)(ctx->r15))

#define BPF_SET_RAX(ctx, value) BPF_SET_REG_64(ctx, ax, value)
#define BPF_SET_RBX(ctx, value) BPF_SET_REG_64(ctx, bx, value)
#define BPF_SET_RCX(ctx, value) BPF_SET_REG_64(ctx, cx, value)
#define BPF_SET_RDX(ctx, value) BPF_SET_REG_64(ctx, dx, value)

// 32-bit registers
#define BPF_EAX(ctx) (u32)((u64)(ctx->ax) & BPF_32BIT_MASK)
#define BPF_EBX(ctx) (u32)((u64)(ctx->bx) & BPF_32BIT_MASK)
#define BPF_ECX(ctx) (u32)((u64)(ctx->cx) & BPF_32BIT_MASK)
#define BPF_EDX(ctx) (u32)((u64)(ctx->dx) & BPF_32BIT_MASK)
#define BPF_ESI(ctx) (u32)((u64)(ctx->si) & BPF_32BIT_MASK)
#define BPF_EDI(ctx) (u32)((u64)(ctx->di) & BPF_32BIT_MASK)
#define BPF_EBP(ctx) (u32)((u64)(ctx->bp) & BPF_32BIT_MASK)
#define BPF_ESP(ctx) (u32)((u64)(ctx->sp) & BPF_32BIT_MASK)
#define BPF_EIP(ctx) (u32)((u64)(ctx->ip) & BPF_32BIT_MASK)
#define BPF_EFLAGS(ctx) (u32)((u64)(ctx->flags) & BPF_32BIT_MASK)
#define BPF_ECS(ctx) (u32)((u64)(ctx->cs) & BPF_32BIT_MASK)
#define BPF_ESS(ctx) (u32)((u64)(ctx->ss) & BPF_32BIT_MASK)

#define BPF_SET_EAX(ctx, value) BPF_SET_REG_32(ctx, ax, value)
#define BPF_SET_EBX(ctx, value) BPF_SET_REG_32(ctx, bx, value)
#define BPF_SET_ECX(ctx, value) BPF_SET_REG_32(ctx, cx, value)
#define BPF_SET_EDX(ctx, value) BPF_SET_REG_32(ctx, dx, value)
#define BPF_SET_ESI(ctx, value) BPF_SET_REG_32(ctx, si, value)

#define BPF_16BIT_MASK 0x0000ffff
// 16-bit registers
#define BPF_AX(ctx) (u16)((u64)(ctx->ax) & BPF_16BIT_MASK)
#define BPF_BX(ctx) (u16)((u64)(ctx->bx) & BPF_16BIT_MASK)
#define BPF_CX(ctx) (u16)((u64)(ctx->cx) & BPF_16BIT_MASK)
#define BPF_DX(ctx) (u16)((u64)(ctx->dx) & BPF_16BIT_MASK)
#define BPF_SI(ctx) (u16)((u64)(ctx->si) & BPF_16BIT_MASK)
#define BPF_DI(ctx) (u16)((u64)(ctx->di) & BPF_16BIT_MASK)
#define BPF_BP(ctx) (u16)((u64)(ctx->bp) & BPF_16BIT_MASK)
#define BPF_SP(ctx) (u16)((u64)(ctx->sp) & BPF_16BIT_MASK)

#define BPF_SET_AX(ctx, value) BPF_SET_REG_16(ctx, ax, value)
#define BPF_SET_BX(ctx, value) BPF_SET_REG_16(ctx, bx, value)
#define BPF_SET_CX(ctx, value) BPF_SET_REG_16(ctx, cx, value)
#define BPF_SET_DX(ctx, value) BPF_SET_REG_16(ctx, dx, value)

// https://en.wikipedia.org/wiki/FLAGS_register
#define BPF_CF_MASK 0x0001
#define BPF_ZF_MASK 0x0040
#define BPF_SF_MASK 0x0080
#define BPF_OF_MASK 0x0800

#define BPF_CF(ctx) ((u64)(ctx->flags) & BPF_CF_MASK)
#define BPF_ZF(ctx) ((u64)(ctx->flags) & BPF_ZF_MASK)
#define BPF_SF(ctx) ((u64)(ctx->flags) & BPF_SF_MASK)
#define BPF_OF(ctx) ((u64)(ctx->flags) & BPF_OF_MASK)

#define BPF_SET_CF_TRUE(ctx)                                                   \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags |= BPF_CF_MASK;                                                      \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)

#define BPF_SET_CF_FALSE(ctx)                                                  \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags &= ~BPF_CF_MASK;                                                     \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)

// ZF = 1 or CF = 1, then jump
#define BPF_SET_JBE_TRUE(ctx)                                                  \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags |= BPF_CF_MASK;                                                      \
    flags |= BPF_ZF_MASK;                                                      \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)

// ZF = 0 and CF = 0, then not jump
#define BPF_SET_JBE_FALSE(ctx)                                                 \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags &= ~BPF_ZF_MASK;                                                     \
    flags &= ~BPF_CF_MASK;                                                     \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)

// ZF=1 or SF!=OF, then jump
#define BPF_SET_JLE_TRUE(ctx)                                                  \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags |= BPF_ZF_MASK;                                                      \
    flags |= BPF_SF_MASK;                                                      \
    flags &= ~BPF_OF_MASK;                                                     \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)
// ZF!=1 and SF==OF, the not jump
#define BPF_SET_JLE_FALSE(ctx)                                                 \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags &= ~BPF_ZF_MASK;                                                     \
    flags &= ~BPF_SF_MASK;                                                     \
    flags &= ~BPF_OF_MASK;                                                     \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)

// CF = 0 and ZF = 0
#define BPF_JA(ctx) (BPF_CF(ctx) == 0 && BPF_ZF(ctx) == 0)
#define BPF_SET_JA_TRUE(ctx)                                                  \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags &= ~BPF_CF_MASK;                                                     \
    flags &= ~BPF_ZF_MASK;                                                     \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)

// Set CF = 1 to make JA false
#define BPF_SET_JA_FALSE(ctx)                                                  \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags |= BPF_CF_MASK;                                                      \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)

// ZF = 0 and SF = OF
#define BPF_JG(ctx) (BPF_ZF(ctx) == 0 && BPF_SF(ctx) == BPF_OF(ctx))
// Set  to make JG true
#define BPF_SET_JG_TRUE(ctx)                                                   \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags &= ~BPF_ZF_MASK;                                                     \
    flags &= ~BPF_SF_MASK;                                                     \
    flags &= ~BPF_OF_MASK;                                                     \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)

// Set ZF = 1 to make JG false
#define BPF_SET_JG_FALSE(ctx)                                                  \
  do {                                                                         \
    u64 flags = BPF_EFLAGS(ctx);                                               \
    flags |= BPF_ZF_MASK;                                                      \
    kfuncs_probe_write_kernel(&ctx->flags, sizeof(flags), &flags,              \
                              sizeof(flags));                                  \
  } while (0)

/**
 * @brief Dump all registers in ctx
 *
 * @param ctx
 */
static __always_inline void dump_ctx(struct pt_regs *ctx) {
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