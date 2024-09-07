// hello.c

#include <linux/init.h>       // Macros for module initialization
#include <linux/module.h>     // Core header for loading LKMs into the kernel
#include <linux/kernel.h>     // For printk()

// this example uses legacy init_module and cleanup_module functions instead of newer module_init and module_exit macros

// Function executed when the module is loaded
int init_module(void)
{
    printk(KERN_WARNING "Hello, world!\n");
    return 0; // Return 0 means successful loading
}

// Function executed when the module is removed
void cleanup_module(void)
{
    printk(KERN_INFO "Goodbye, world!\n");
}

// Specify the functions to be run on module load and removal

MODULE_LICENSE("MIT");
MODULE_AUTHOR("Wes");
MODULE_DESCRIPTION("Hello World Module");
MODULE_VERSION("0.1");
