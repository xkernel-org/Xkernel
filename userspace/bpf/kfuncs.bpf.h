#ifndef __KFUNCS_H__
#define __KFUNCS_H__

// extern int kfuncs_probe_write_kernel(void *dst, __u32 dst_sz, const void *src, __u32 src_sz) __ksym;
extern int kfuncs_probe_write_kernel(void) __ksym;

#endif
