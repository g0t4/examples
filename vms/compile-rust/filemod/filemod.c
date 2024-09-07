// hello.c

#include <linux/init.h>       // Macros for module initialization
#include <linux/module.h>     // Core header for loading LKMs into the kernel
#include <linux/kernel.h>     // For printk()

// Function executed when the module is loaded
static int __init hello_init(void)
{
    // KERN_WARNING/INFO/etc are marcros => see include/linux/kern_levels.h
    // btw in C, string literals separated by whitespace are concatenated ... so printk is called with one big string:
    printk(KERN_WARNING "Hello, world!  " "foo\n"); // KERN_WARNING is a macro => "4" thus setting the priority level
    printk("Hello, 2\n");
    printk("\001" "6Hello, 3\n"); // pass priority w/o macros KERN_INFO => KERN_SOH "6" => "\001" "6"
    return 0; // Return 0 means successful loading
}

// Function executed when the module is removed
static void __exit hello_exit(void)
{
    printk(KERN_INFO "Goodbye, world!\n");
}

// Specify the functions to be run on module load and removal
module_init(hello_init);
module_exit(hello_exit);

MODULE_LICENSE("MIT");
MODULE_AUTHOR("Wes");
MODULE_DESCRIPTION("Hello World Module");
MODULE_VERSION("0.1");
