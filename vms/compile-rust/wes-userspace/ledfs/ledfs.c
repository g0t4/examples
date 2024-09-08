#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/device.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>
#include <linux/gpio.h>
#include <linux/delay.h>
#include <linux/interrupt.h>
#include "pins.h"

#define USE_GLOBAL_LINE_NUMBER RPI5_GPIO_17

static int set_led_to(bool enabled)
{
    // probably don't need gpio_is_valid
    if (gpio_is_valid(USE_GLOBAL_LINE_NUMBER))
    {
        // PRN if there is overhead in set direction each time, then detect direction before setting it in case not needed...
        if (gpio_direction_output(USE_GLOBAL_LINE_NUMBER, enabled) < 0)
        {
            pr_err("ledfs: gpio_direction_output failed\n");
            return -1;
        }
        pr_info("ledfs: LED turned %s\n", enabled ? "on" : "off");
        return 0;
    }
    else
    {
        pr_err("ledfs: Invalid GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);
        return -EINVAL;
    }
}

static ssize_t ledfs_read_data(struct file *file, char __user *buf, size_t len, loff_t *offset)
{
    int value = gpio_get_value(USE_GLOBAL_LINE_NUMBER);

    // return "on" or "off" based on GPIO pin value
    char *data = (value == 1) ? "on\n" : "off\n";

    size_t datalen = strlen(data);
    return simple_read_from_buffer(buf, len, offset, data, datalen);
}

static ssize_t ledfs_write_data(struct file *file, const char __user *buf, size_t len, loff_t *offset)
{
    char *data = kzalloc(len + 1, GFP_KERNEL);
    if (!data)
        return -ENOMEM;

    if (copy_from_user(data, buf, len))
    {
        kfree(data);
        return -EFAULT;
    }

    if (strncmp(data, "on", 2) == 0)
        set_led_to(1);
    else if (strncmp(data, "off", 3) == 0)
        set_led_to(0);

    kfree(data);
    return len;
}

static const struct file_operations ledfs_fops = {
    .owner = THIS_MODULE,
    .read = ledfs_read_data,
    .write = ledfs_write_data,
};

static int major;
static struct class *ledfs_class = NULL;
static struct device *ledfs_device = NULL;
static bool do_request_gpio = false; // skip request/free methods for now
static bool do_pin_tests = true;
static int do_pin_tests_msdelay = 1000;

static int __init ledfs_init(void)
{
    if (do_pin_tests)
    {
        if (gpio_is_valid(USE_GLOBAL_LINE_NUMBER))
        {
            pr_info("ledfs: Using GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);
        }
        else
        {
            pr_err("ledfs: Invalid GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);
            return -EINVAL;
        }

        pr_info("ledfs: GPIO pin %d value is %d\n", USE_GLOBAL_LINE_NUMBER, gpio_get_value(USE_GLOBAL_LINE_NUMBER));
        msleep(do_pin_tests_msdelay);

        set_led_to(1);
        pr_info("ledfs: GPIO pin %d value is %d (after set 1)\n", USE_GLOBAL_LINE_NUMBER, gpio_get_value(USE_GLOBAL_LINE_NUMBER));
        msleep(do_pin_tests_msdelay);

        set_led_to(0);
        pr_info("ledfs: GPIO pin %d value is %d (after set 0)\n", USE_GLOBAL_LINE_NUMBER, gpio_get_value(USE_GLOBAL_LINE_NUMBER));
        msleep(do_pin_tests_msdelay);
    }

    if (do_request_gpio)
    {
        pr_info("ledfs: Requesting GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);
        // ! is it possible gpio_request is resetting the value to 1? (i.e. active-high bias)... was that part of my issue with trying to find what reset my value, I know at the time I was still calling this (failed module load) and so maybe this was doing that?
        // if this fails, can I just ignore it? some of the guides I saw said it is not enforced? ...
        int ret = gpio_request(4, "ledfs_pin"); // IIUC, ledfs_pin label maps to /sys fs somewhere?
        if (ret)
        {
            // gpio_request failed with error -517 // currently, but I have not vetted if 4 is appropriate for RPI
            pr_err("ledfs: gpio_request failed with error %d\n", ret);
            return ret;
        }
        // PRN need to export/unexport? would it help to do this to test via sysfs debug fs (IIUC that makes this possible)... also wondering if setting label with request + export then results in that label showing in the output of the command `gpioinfo`? (instead of "unused")... note unused seems to be a column for a second label of sorts which I speculate is from when it is exported? and first requested? or?
    }

    // Register the character device
    major = register_chrdev(0, "ledfs", &ledfs_fops);
    if (major < 0)
    {
        pr_err("ledfs: Unable to register character device\n");
        gpio_free(USE_GLOBAL_LINE_NUMBER);
        return major;
    }

    // Create the device class
    ledfs_class = class_create("ledfs");
    if (IS_ERR(ledfs_class))
    {
        unregister_chrdev(major, "ledfs");
        pr_err("ledfs: Failed to create class\n");
        if (do_request_gpio)
            gpio_free(USE_GLOBAL_LINE_NUMBER);
        return PTR_ERR(ledfs_class);
    }

    // Create the device file /dev/ledfs
    ledfs_device = device_create(ledfs_class, NULL, MKDEV(major, 0), NULL, "ledfs");
    if (IS_ERR(ledfs_device))
    {
        class_destroy(ledfs_class);
        unregister_chrdev(major, "ledfs");
        pr_err("ledfs: Failed to create device\n");
        if (do_request_gpio)
            gpio_free(USE_GLOBAL_LINE_NUMBER);
        return PTR_ERR(ledfs_device);
    }

    pr_info("ledfs: Driver loaded successfully, /dev/ledfs created\n");
    return 0;
}

static void __exit ledfs_exit(void)
{
    // Free the GPIO pin
    if (do_request_gpio)
        gpio_free(USE_GLOBAL_LINE_NUMBER);

    // Remove the device
    device_destroy(ledfs_class, MKDEV(major, 0));

    // Destroy the device class
    class_destroy(ledfs_class);

    // Unregister the character device
    unregister_chrdev(major, "ledfs");

    pr_info("ledfs: Driver unloaded\n");
}

module_init(ledfs_init);
module_exit(ledfs_exit);

MODULE_LICENSE("GPL"); // IF incompatible with other used modules, then compile fails! i.e. MIT here fails compile!
MODULE_AUTHOR("Wes");
MODULE_DESCRIPTION("/dev_num/ledfs driver");
MODULE_VERSION("0.1");
