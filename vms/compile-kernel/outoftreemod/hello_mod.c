#include <linux/module.h>   // Needed for all kernel modules
#include <linux/init.h>     // Needed for the macros

// Function called when the module is loaded into the kernel
static int __init hello_init(void)
{
    printk(KERN_INFO "Hello, World!\n");
    return 0;  // Return 0 to indicate successful loading
}

// Function called when the module is removed from the kernel
static void __exit hello_exit(void)
{
    printk(KERN_INFO "Goodbye, World!\n");
}

// Macros to define the entry and exit points of the module
module_init(hello_init);
module_exit(hello_exit);

// Module metadata
MODULE_LICENSE("GPL");              // License type
MODULE_AUTHOR("Your Name");         // Author information
MODULE_DESCRIPTION("A simple Hello World module");  // Description
MODULE_VERSION("1.0");              // Version of the module

