#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/sched.h>

// Define the fits_capacity macro exactly as in the kernel
#define fits_capacity(cap, max)	((cap) * 1280 < (max) * 1024)

// Test arguments structure to prevent compile-time optimization
struct test_args {
    unsigned long cap1, max1;
    unsigned long cap2, max2;
    unsigned long cap3, max3;
    unsigned long cap4, max4;
    unsigned long cap5, max5;
    unsigned long cap6, max6;
    unsigned long cap7, max7;
    unsigned long cap8, max8;
    unsigned long cap9, max9;
    unsigned long cap10, max10;
    unsigned long cap11, max11;
    unsigned long cap12, max12;
    unsigned long cap13, max13;
    unsigned long cap14, max14;
    unsigned long cap15, max15;
    unsigned long cap16, max16;
    unsigned long cap17, max17;
    unsigned long cap18, max18;
    unsigned long cap19, max19;
    unsigned long cap20, max20;
};

volatile struct test_args test_args_inst;
volatile int fits_capacity_result = 0;

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Assembly Test");
MODULE_DESCRIPTION("Test fits_capacity macro assembly output");

// Test function 1: Simple capacity comparison
int test_simple_capacity(void)
{
    unsigned long capacity = test_args_inst.cap1;
    unsigned long max_capacity = test_args_inst.max1;
    
    if (fits_capacity(capacity, max_capacity)) {
        return 1;  // Fits
    }
    return 0;     // Doesn't fit
}
EXPORT_SYMBOL(test_simple_capacity);

// Test function 2: Multiple comparisons in a loop
int test_capacity_loop(void)
{
    unsigned long capacities[] = {
        test_args_inst.cap2, test_args_inst.cap3, test_args_inst.cap4, 
        test_args_inst.cap5, test_args_inst.cap6
    };
    unsigned long max_cap = test_args_inst.max2;
    int i, count = 0;
    
    for (i = 0; i < 5; i++) {
        if (fits_capacity(capacities[i], max_cap)) {
            count++;
        }
    }
    
    return count;
}
EXPORT_SYMBOL(test_capacity_loop);

// Test function 3: Conditional assignment
unsigned long test_conditional_assign(unsigned long util, unsigned long max)
{
    unsigned long result;
    
    if (fits_capacity(util, max)) {
        result = util * 2;  // Double if fits
    } else {
        result = max;       // Use max if doesn't fit
    }
    
    return result;
}
EXPORT_SYMBOL(test_conditional_assign);

// Test function 4: Complex expression with fits_capacity
int test_complex_expression(unsigned long load, unsigned long capacity)
{
    unsigned long threshold = capacity * 3 / 4;  // 75% of capacity
    
    // Complex condition using fits_capacity
    if (fits_capacity(load, capacity) && load > threshold) {
        return 1;  // High load but still fits
    }
    
    return 0;
}
EXPORT_SYMBOL(test_complex_expression);

// Test function 5: Nested fits_capacity calls
int test_nested_capacity(unsigned long util1, unsigned long util2, 
                               unsigned long max1, unsigned long max2)
{
    // Check if both utilities fit in their respective capacities
    if (fits_capacity(util1, max1) && fits_capacity(util2, max2)) {
        return 1;  // Both fit
    }
    
    // Check if at least one fits
    if (fits_capacity(util1, max1) || fits_capacity(util2, max2)) {
        return 2;  // At least one fits
    }
    
    return 0;  // Neither fits
}
EXPORT_SYMBOL(test_nested_capacity);

// Test function 6: fits_capacity in arithmetic expression
unsigned long test_arithmetic_with_capacity(unsigned long util, unsigned long max)
{
    // Use fits_capacity result in arithmetic
    unsigned long multiplier = fits_capacity(util, max) ? 2 : 1;
    return util * multiplier;
}
EXPORT_SYMBOL(test_arithmetic_with_capacity);

// Test function 7: fits_capacity with different data types
int test_different_types(void)
{
    int int_cap = (int)test_args_inst.cap7;
    int int_max = (int)test_args_inst.max7;
    unsigned long ul_cap = test_args_inst.cap8;
    unsigned long ul_max = test_args_inst.max8;
    
    int result1 = fits_capacity(int_cap, int_max);
    int result2 = fits_capacity(ul_cap, ul_max);
    
    return result1 + result2;
}
EXPORT_SYMBOL(test_different_types);

// Test function 8: fits_capacity with constants (now using struct values)
int test_with_constants(void)
{
    // Test with various constant combinations from struct
    int result = 0;
    
    result += fits_capacity(test_args_inst.cap9, test_args_inst.max9);
    result += fits_capacity(test_args_inst.cap10, test_args_inst.max10);
    result += fits_capacity(test_args_inst.cap11, test_args_inst.max11);
    result += fits_capacity(test_args_inst.cap12, test_args_inst.max12);
    
    return result;
}
EXPORT_SYMBOL(test_with_constants);

// Test function 9: fits_capacity in switch statement
int test_switch_capacity(unsigned long util, unsigned long max)
{
    switch (fits_capacity(util, max)) {
        case 1:
            return 100;  // Fits
        case 0:
            return 200;  // Doesn't fit
        default:
            return 300;  // Unexpected
    }
}
EXPORT_SYMBOL(test_switch_capacity);

// Test function 10: fits_capacity with function calls
unsigned long get_capacity(void) { return test_args_inst.cap13; }
unsigned long get_max_capacity(void) { return test_args_inst.max13; }
EXPORT_SYMBOL(get_capacity);
EXPORT_SYMBOL(get_max_capacity);

int test_with_function_calls(void)
{
    return fits_capacity(get_capacity(), get_max_capacity());
}
EXPORT_SYMBOL(test_with_function_calls);

// Test function 11: Multiple fits_capacity calls with different values
int test_multiple_capacity_checks(void)
{
    int result = 0;
    
    result += fits_capacity(test_args_inst.cap14, test_args_inst.max14);
    result += fits_capacity(test_args_inst.cap15, test_args_inst.max15);
    result += fits_capacity(test_args_inst.cap16, test_args_inst.max16);
    result += fits_capacity(test_args_inst.cap17, test_args_inst.max17);
    result += fits_capacity(test_args_inst.cap18, test_args_inst.max18);
    result += fits_capacity(test_args_inst.cap19, test_args_inst.max19);
    result += fits_capacity(test_args_inst.cap20, test_args_inst.max20);
    
    return result;
}
EXPORT_SYMBOL(test_multiple_capacity_checks);

// Module initialization function
static int __init fits_capacity_asm_init(void)
{
    printk(KERN_INFO "fits_capacity assembly test module loaded\n");
    
    // Initialize test arguments with various values
    test_args_inst.cap1 = 800; test_args_inst.max1 = 1024;
    test_args_inst.cap2 = 500; test_args_inst.max2 = 1024;
    test_args_inst.cap3 = 800; test_args_inst.max3 = 1024;
    test_args_inst.cap4 = 900; test_args_inst.max4 = 1024;
    test_args_inst.cap5 = 1000; test_args_inst.max5 = 1024;
    test_args_inst.cap6 = 1200; test_args_inst.max6 = 1024;
    test_args_inst.cap7 = 800; test_args_inst.max7 = 1024;
    test_args_inst.cap8 = 900; test_args_inst.max8 = 1024;
    test_args_inst.cap9 = 512; test_args_inst.max9 = 1024;
    test_args_inst.cap10 = 1024; test_args_inst.max10 = 1024;
    test_args_inst.cap11 = 1280; test_args_inst.max11 = 1024;
    test_args_inst.cap12 = 800; test_args_inst.max12 = 1024;
    test_args_inst.cap13 = 800; test_args_inst.max13 = 1024;
    test_args_inst.cap14 = 600; test_args_inst.max14 = 1024;
    test_args_inst.cap15 = 700; test_args_inst.max15 = 1024;
    test_args_inst.cap16 = 800; test_args_inst.max16 = 1024;
    test_args_inst.cap17 = 900; test_args_inst.max17 = 1024;
    test_args_inst.cap18 = 1000; test_args_inst.max18 = 1024;
    test_args_inst.cap19 = 1100; test_args_inst.max19 = 1024;
    test_args_inst.cap20 = 1200; test_args_inst.max20 = 1024;
    
    // Call all test functions to ensure they're compiled and accumulate result
    fits_capacity_result = test_simple_capacity();
    fits_capacity_result += test_capacity_loop();
    fits_capacity_result += test_conditional_assign(test_args_inst.cap1, test_args_inst.max1);
    fits_capacity_result += test_complex_expression(test_args_inst.cap2, test_args_inst.max2);
    fits_capacity_result += test_nested_capacity(test_args_inst.cap3, test_args_inst.cap4, 
                                                test_args_inst.max3, test_args_inst.max4);
    fits_capacity_result += test_arithmetic_with_capacity(test_args_inst.cap5, test_args_inst.max5);
    fits_capacity_result += test_different_types();
    fits_capacity_result += test_with_constants();
    fits_capacity_result += test_switch_capacity(test_args_inst.cap6, test_args_inst.max6);
    fits_capacity_result += test_with_function_calls();
    fits_capacity_result += test_multiple_capacity_checks();
    
    printk(KERN_INFO "All test functions executed successfully, result=%d\n", fits_capacity_result);
    return 0;
}

// Module cleanup function
static void __exit fits_capacity_asm_exit(void)
{
    printk(KERN_INFO "fits_capacity assembly test module unloaded\n");
}

module_init(fits_capacity_asm_init);
module_exit(fits_capacity_asm_exit); 