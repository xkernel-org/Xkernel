#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/text-patching.h>
#include <linux/param.h>

#define MAX_INSN_LEN 16

static ulong target_addr = 0;
module_param(target_addr, ulong, 0644);
MODULE_PARM_DESC(target_addr, "Target instruction address");

static unsigned char new_insn[MAX_INSN_LEN];
static int new_insn_len;
module_param_array(new_insn, byte, &new_insn_len, 0644);
MODULE_PARM_DESC(new_insn, "Byte array for new instruction");

static unsigned char orig_insn[MAX_INSN_LEN];

static int __init my_init(void)
{
    if (!target_addr || new_insn_len == 0) {
        pr_err("Missing target_addr or new_insn!\n");
        return -EINVAL;
    }

    memcpy(orig_insn, (void *)target_addr, new_insn_len);  // save original

    pr_info("Patching %d bytes at %px\n", new_insn_len, (void *)target_addr);
    text_poke((void *)target_addr, new_insn, new_insn_len);
    return 0;
}

static void __exit my_exit(void)
{
    if (new_insn_len > 0) {
        text_poke((void *)target_addr, orig_insn, new_insn_len);  // restore
        pr_info("Restoring %d bytes at %px\n", new_insn_len, (void *)target_addr);
    }
}

module_init(my_init);
module_exit(my_exit);
MODULE_LICENSE("GPL");
