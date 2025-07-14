#ifndef __KFUNCS_H__
#define __KFUNCS_H__

extern long kfuncs_probe_write_kernel(void *dst__ign, __u32 dst_sz,
                                     const void *src__ign, __u32 src_sz) __ksym;
extern int kfuncs_text_poke(void *addr__ign, void *insn__ign, __u32 insn_len__sz) __ksym;
#endif
