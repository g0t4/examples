#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/device.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>

static int major;
static struct class *my_class;
static struct cdev my_cdev;

static int dht22_open(struct inode *inode, struct file *file) {
    pr_info("dht22_open opened\n");
    return 0;
}

static int dht22_release(struct inode *inode, struct file *file) {
    pr_info("dht22_release closed\n");
    return 0;
}


static ssize_t cached_value = 10;

static ssize_t dht22_read(struct file *file, char __user *buf, size_t len, loff_t *offset) {
    pr_info("dht22_read called\n");
    return cached_value;
}

static ssize_t dht22_write(struct file *file, const char __user *buf, size_t len, loff_t *offset) {
    pr_info("dht22_write called\n");
    return len;
}

static struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = dht22_open,
    .release = dht22_release,
    .read = dht22_read,
    .write = dht22_write,
};

static int __init dht22_init(void)
{
    // allocate chrdev region
    dev_t dev_num;

    int ret = alloc_chrdev_region(&dev_num, 0, 1, "dht22");
    if (ret < 0)
    {
        printk(KERN_ERR "Failed to allocate chrdev region\n");
        return ret;
    }

    major = MAJOR(dev_num);
    printk(KERN_INFO "Allocated chrdev region: %d\n", major);

    // create/register cdev

    cdev_init(&my_cdev, &fops);
    my_cdev.owner = THIS_MODULE;

    if (cdev_add(&my_cdev, dev_num, 1) < 0)
    {
        unregister_chrdev_region(dev_num, 1);
        return -1;
    }

    // create device node
    my_class = class_create("dht22_class");
    if (IS_ERR(my_class))
    {
        cdev_del(&my_cdev);
        unregister_chrdev_region(dev_num, 1);
        return PTR_ERR(my_class);
    }

    device_create(my_class, NULL, dev_num, NULL, "dht22");

    return 0;
}

static void __exit dht22_exit(void)
{
    // destroy device node
    dev_t dev_num = MKDEV(major, 0);
    device_destroy(my_class, dev_num);
    class_destroy(my_class);

    // unregister cdev
    cdev_del(&my_cdev);

    // unregister chrdev region
    unregister_chrdev_region(dev_num, 1);

    printk(KERN_INFO "Unregistered chrdev region: %d\n", major);
}

module_init(dht22_init);
module_exit(dht22_exit);

MODULE_LICENSE("GPL"); // IF incompatible with other used modules, then compile fails! i.e. MIT here fails compile!
MODULE_AUTHOR("Wes");
MODULE_DESCRIPTION("/dev_num/dht22 driver");
MODULE_VERSION("0.1");
