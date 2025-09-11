MMAP_LOTSAMISS - mmap readahead

NODE_RECLAIM_PRIORITY - memory reclaim

ADAPT_SCALE_BASE - hash table vs memory size

***
dirty_background_ratio - background flush

It can be adjusted with `sysctl`:
```c
static const struct ctl_table vm_page_writeback_sysctls[] = {
	{
		.procname   = "dirty_background_ratio",
		.data       = &dirty_background_ratio,
        ...
    }
    ...
}
```
***

slub related (/mm/slub.c) - only kernel general purpose allocator
swap_ra related - swap space readahead

***
unknown:
z-bud 
z3fold
zsmalloc

ksm
migration
compaction

PVM_MAX_KMALLOC_PAGES
BLOOM_FILTER_SHIFT