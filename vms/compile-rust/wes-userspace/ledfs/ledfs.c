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

static ssize_t ledfs_read_data(struct file *file, char __user *buf, size_t len, loff_t *offset)
{
    int value = gpio_get_value(USE_GLOBAL_LINE_NUMBER);

    // return "on" or "off" based on GPIO pin value
    char *data = (value == 0) ? "on\n" : "off\n";

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

    // set GPIO pin value based on input data
    if (strncmp(data, "on", 2) == 0)
        gpio_set_value(USE_GLOBAL_LINE_NUMBER, 1);
    else if (strncmp(data, "off", 3) == 0)
        gpio_set_value(USE_GLOBAL_LINE_NUMBER, 0);

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

static int __init ledfs_init(void)
{
    if (do_pin_tests)
    {
        pr_info("ledfs: Testing GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);

        // just get a damn pin
        if (gpio_is_valid(USE_GLOBAL_LINE_NUMBER))
        {
            // OMG this returns true
            pr_info("ledfs: Using GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);
        }
        else
        {
            pr_err("ledfs: Invalid GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);
            return -EINVAL;
        }
        // int  gpio_get_value(unsigned gpio); // *** WORKING (matches values from cli `gpioget` command for ports 4 thru 9, confirmed 9 shows 0 and 7,8,4 show 1 just like `gpioget`)
        int value = gpio_get_value(USE_GLOBAL_LINE_NUMBER); // matches gpioget gpiochip4 X for a range of #s!
        pr_info("ledfs: GPIO pin %d value is %d\n", USE_GLOBAL_LINE_NUMBER, value);
        msleep(1); // *** WORKING (confirmed with `gpioget` command)

        // void gpio_set_value(unsigned int gpio, int value);
        gpio_set_value(USE_GLOBAL_LINE_NUMBER, 1); // WORKING within this code, just know that external forces seem to reset it when I go to inspect it with CLI `gpioget` command

        int value2 = gpio_get_value(USE_GLOBAL_LINE_NUMBER); // SHOWS SET WORKS, before smth else reverts it... is it reverting b/c active-high bias? (i.e. pull-up resistor)... probably because hardware is missing and so its floating or otherwise unpredictable... TLDR I think I am good to go to test this driver tomorrow.
        // !!! TLDR I think I am good to go w/o using gpio_request... it appears to be working and likely works better once I hook up actual hardware with pull up resister, ledfs, etc!!!
        pr_info("ledfs: GPIO pin %d value is %d\n", USE_GLOBAL_LINE_NUMBER, value2);
        msleep(1);
        // *** WTF IT IS CHANGING NOW... OMG READING IT WITH `gpioget` reverts the value to 1!

        // int gpio_export(unsigned int gpio, bool direction_may_change);
        // int gpio_unexport(unsigned int gpio);

        // int  gpio_direction_input(unsigned gpio)
        // int  gpio_direction_output(unsigned gpio, int value)
        if (gpio_direction_output(USE_GLOBAL_LINE_NUMBER, 0) < 0) // CONFIRMED VALUE IS SET!
        {
            // OMFG it worked, I flipped GPIO7 to output!!!
            // sudo gpioinfo gpiochip4  | grep "GPIO\d"
            // first 10: // sudo gpioinfo gpiochip4  | grep "GPIO[[:digit:]]\b"
            pr_err("ledfs: gpio_direction_output failed\n");
            return -1;
        }
        int value3 = gpio_get_value(USE_GLOBAL_LINE_NUMBER);
        pr_info("ledfs: GPIO pin %d value is %d (after output dir)\n", USE_GLOBAL_LINE_NUMBER, value3);
        msleep(1);

        gpio_set_value(USE_GLOBAL_LINE_NUMBER, 1); // WORKING TOO
        int value4 = gpio_get_value(USE_GLOBAL_LINE_NUMBER);
        pr_info("ledfs: GPIO pin %d value is %d (after set 1)\n", USE_GLOBAL_LINE_NUMBER, value4);
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
