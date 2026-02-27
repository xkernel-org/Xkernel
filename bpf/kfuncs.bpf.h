#ifndef __KFUNCS_H__
#define __KFUNCS_H__

extern long bpf_probe_write_kernel(void *dst__ign, __u32 dst__sz,
                                     const void *src__ign) __ksym;

// Wrapper for bpf_probe_write_kernel: SIE write helper
static __always_inline long sie_write_kernel(void *dst, __u32 size, const void *src) {
    return bpf_probe_write_kernel(dst, size, src);
}

#endif
