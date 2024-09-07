// hello.c

#include <linux/init.h>       // Macros for module initialization
#include <linux/module.h>     // Core header for loading LKMs into the kernel
#include <linux/kernel.h>     // For printk()

// Function executed when the module is loaded
static int __init hello_init(void)
{
    printk(KERN_INFO "Hello, world!\n");
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

MODULE_LICENSE("GPL");             // License type
MODULE_AUTHOR("Your Name");        // Module author
MODULE_DESCRIPTION("A simple Hello World LKM");  // Module description
MODULE_VERSION("0.1");             // Version number
