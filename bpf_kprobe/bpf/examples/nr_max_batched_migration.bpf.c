// SPDX-License-Identifier: GPL-2.0
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "xkernel.bpf.h"

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key, u32);
    __type(value, u64);
    __uint(max_entries, 1);
} total_hits_map SEC(".maps");

volatile __u64 g_last_print_ns;
#define INTERVAL_NS (5ull * 1000 * 1000 * 1000)

static __always_inline void update_counter() {
    u32 key = 0;
    u64 *val = bpf_map_lookup_elem(&total_hits_map, &key);
    if (val) {
        __sync_fetch_and_add(val, 1);
    }
}

static __always_inline void check_and_print() {
    u64 now = bpf_ktime_get_ns();
    if (now - g_last_print_ns >= INTERVAL_NS) {
        g_last_print_ns = now;
        
        u32 key = 0;
        u64 *val = bpf_map_lookup_elem(&total_hits_map, &key);
        if (val) {
            bpf_printk("Alive: current total hits = %llu\n", *val);
        }
    }
}

SEC("kprobe/migrate_pages+0x117")
int BPF_KPROBE(migrate_pages_0x117){
    BPF_SET_JG_FALSE(ctx);
    
    // update_counter();
    // check_and_print();

    int eax = (int)BPF_EAX(ctx);

    // if(eax > 1023){
    if(eax > 511){
    // if(eax > 255){
    // if(eax > 127){
    // if(eax > 63){
    // if(eax > 31){
        BPF_SET_JG_TRUE(ctx);
    }
    
    return 0;
}

SEC("kprobe/migrate_pages+0x164")
int BPF_KPROBE(migrate_pages_0x164){
    BPF_SET_JG_FALSE(ctx);
    
    // update_counter();
    // check_and_print();

    int edx = (int)BPF_EDX(ctx); 
    
    // if(edx > 1023){
    if(edx > 511){
    // if(edx > 255){
    // if(edx > 127){
    // if(edx > 63){
    // if(edx > 31){
        BPF_SET_JG_TRUE(ctx);
    }
    
    return 0;
}
