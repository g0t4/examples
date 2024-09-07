#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>

static int __init dht22_init(void)
{
    return 0;
}

static void __exit dht22_exit(void)
{
}

module_init(dht22_init);
module_exit(dht22_exit);

MODULE_LICENSE("MIT");
MODULE_AUTHOR("Wes");
MODULE_DESCRIPTION("/dev/dht22 driver");
MODULE_VERSION("0.1");
