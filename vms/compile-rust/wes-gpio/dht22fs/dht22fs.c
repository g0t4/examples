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
#include "../ledfs/pins.h"

#define USE_GLOBAL_LINE_NUMBER RPI5_GPIO_17 // TODO what pin?
// 1 = VCC (3.3V)
// 2 = DATA (GPIO)
// 3 = NC (not connected)
// 4 = GND

struct dht22_data
{
    int temperature;
    int humidity;
};

static struct dht22_data sensor_data;

static int dht22_read(void)
{
    // TODO lock for one read at a time?
    // TODO fail if read too soon after last read? (IIUC 2 second probing interval minimum required)

    // FYI protocol http://www.ocfreaks.com/basics-interfacing-dht11-dht22-humidity-temperature-sensor-mcu/
    // http://www.ocfreaks.com/imgs/embedded/dht/dhtxx_protocol.png

    int data[5] = {0}; // 5 bytes (8 bits) of data (humidity and temperature) => can use short instead of int
    int i, j;

    // Send the start signal to DHT22
    gpio_direction_output(USE_GLOBAL_LINE_NUMBER, 1); // pull high
    udelay(20);                                       // for 20us (not sure this needs to be 20us? protocol says pull low for 18us to start?) // TODO does it need to be 20us?
    gpio_direction_output(USE_GLOBAL_LINE_NUMBER, 0); // pull low
    msleep(18);                                       // for at least 18ms (holy crap that is a long long time)
    gpio_direction_output(USE_GLOBAL_LINE_NUMBER, 1); // pull high
    udelay(40);                                       // for 40us (FYI response can come after 20-40us so I guess wait 40us to be safe)

    gpio_direction_input(USE_GLOBAL_LINE_NUMBER); // start reading (can't I start reading right after pull high? or?)

    // Wait for the sensor response (80us low, 80us high)
    while (gpio_get_value(USE_GLOBAL_LINE_NUMBER) == 1)
        ;
    udelay(80); // once low, wait 80us // should we check every 5us instead of just skip 80?!
    while (gpio_get_value(USE_GLOBAL_LINE_NUMBER) == 0)
        ;
    udelay(80); // once high, wait 80us => "get ready" for data transmission

    // Read the data (40 bits) // each bit is 50us low, then high for ... 26-28us => "0", 70us => "1"
    // up to 5ms total if all 1s, ~3ms if all 0s
    for (i = 0; i < 5; i++)
    {
        // 5 bytes of data sent
        for (j = 0; j < 8; j++)
        {
            // 8 bits per byte obviously
            while (gpio_get_value(USE_GLOBAL_LINE_NUMBER) == 0)
                ;       // Wait for the pin to go high, during this time we are in the 50us low start of bit state
            udelay(30); // Delay to determine if it's a '1' or '0'
            // after 30us if it is still high, then it is a '1', otherwise it is a '0'
            if (gpio_get_value(USE_GLOBAL_LINE_NUMBER) == 1)
            {
                data[i] |= (1 << (7 - j)); // Set bit
                while (gpio_get_value(USE_GLOBAL_LINE_NUMBER) == 1)
                    ; // Wait for the pin to go low
            }
        }
    }

    // MSB sent first
    // 40bits of data is divided into 5 bytes
    // Convert data to temperature and humidity
    // 1st Byte: Relative Humidity Integral Data in % (Integer Part)
    // 2nd Byte: Relative Humidity Decimal Data in % (Fractional Part) – Zero for DHT11
    // 3rd Byte: Temperature Integral in Degree Celsius (Integer Part)
    // 4th Byte: Temperature in Decimal Data in % (Fractional Part) – Zero for DHT11
    // 5th Byte: Checksum (Last 8 bits of {1st Byte + 2nd Byte + 3rd Byte+ 4th Byte})

    // check checksum // last byte (8 bits) as each byte is 8 bits (not int size)
    if (data[4] != ((data[0] + data[1] + data[2] + data[3]) & 0xFF))
    {
        pr_err("DHT22: Data checksum error\n");
        return -1;
    }

    sensor_data.humidity = ((data[0] << 8) + data[1]) / 10;
    sensor_data.temperature = (((data[2] & 0x7F) << 8) + data[3]) / 10;
    if (data[2] & 0x80)
    {
        sensor_data.temperature = -sensor_data.temperature; // Handle negative temperature
    }

    return 0;
}

static ssize_t dht22_read_data(struct file *file, char __user *buf, size_t len, loff_t *offset)
{
    char buffer[64];

    if (dht22_read() < 0)
    {
        return -EFAULT; // Error reading sensor
    }

    snprintf(buffer, sizeof(buffer), "Temperature: %d C, Humidity: %d %%\n", sensor_data.temperature, sensor_data.humidity);

    return simple_read_from_buffer(buf, len, offset, buffer, strlen(buffer));
}

static const struct file_operations dht22_fops = {
    .owner = THIS_MODULE,
    .read = dht22_read_data,
};

static int major;
static struct class *dht22_class = NULL;
static struct device *dht22_device = NULL;
static bool do_request_gpio = false; // skip request/free methods for now
static bool do_pin_tests = true;

static int __init dht22_init(void)
{
    if (do_pin_tests)
    {
        pr_info("DHT22: Testing GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);

        // just get a damn pin
        if (gpio_is_valid(USE_GLOBAL_LINE_NUMBER))
        {
            // OMG this returns true
            pr_info("DHT22: Using GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);
        }
        else
        {
            pr_err("DHT22: Invalid GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);
            return -EINVAL;
        }
        // int  gpio_get_value(unsigned gpio); // *** WORKING (matches values from cli `gpioget` command for ports 4 thru 9, confirmed 9 shows 0 and 7,8,4 show 1 just like `gpioget`)
        int value = gpio_get_value(USE_GLOBAL_LINE_NUMBER); // matches gpioget gpiochip4 X for a range of #s!
        pr_info("DHT22: GPIO pin %d value is %d\n", USE_GLOBAL_LINE_NUMBER, value);

        // void gpio_set_value(unsigned int gpio, int value);
        gpio_set_value(USE_GLOBAL_LINE_NUMBER, 1); // WORKING within this code, just know that external forces seem to reset it when I go to inspect it with CLI `gpioget` command

        int value2 = gpio_get_value(USE_GLOBAL_LINE_NUMBER); // SHOWS SET WORKS, before smth else reverts it... is it reverting b/c active-high bias? (i.e. pull-up resistor)... probably because hardware is missing and so its floating or otherwise unpredictable... TLDR I think I am good to go to test this driver tomorrow.
        // !!! TLDR I think I am good to go w/o using gpio_request... it appears to be working and likely works better once I hook up actual hardware with pull up resister, DHT22, etc!!!
        pr_info("DHT22: GPIO pin %d value is %d\n", USE_GLOBAL_LINE_NUMBER, value2);
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
            pr_err("DHT22: gpio_direction_output failed\n");
            return -1;
        }
        int value3 = gpio_get_value(USE_GLOBAL_LINE_NUMBER);
        pr_info("DHT22: GPIO pin %d value is %d (after output dir)\n", USE_GLOBAL_LINE_NUMBER, value3);

        gpio_set_value(USE_GLOBAL_LINE_NUMBER, 1); // WORKING TOO
        int value4 = gpio_get_value(USE_GLOBAL_LINE_NUMBER);
        pr_info("DHT22: GPIO pin %d value is %d (after set 1)\n", USE_GLOBAL_LINE_NUMBER, value4);
    }

    if (do_request_gpio)
    {
        pr_info("DHT22: Requesting GPIO pin %d\n", USE_GLOBAL_LINE_NUMBER);
        // ! is it possible gpio_request is resetting the value to 1? (i.e. active-high bias)... was that part of my issue with trying to find what reset my value, I know at the time I was still calling this (failed module load) and so maybe this was doing that?
        // if this fails, can I just ignore it? some of the guides I saw said it is not enforced? ...
        int ret = gpio_request(4, "dht22_pin"); // IIUC, dht22_pin label maps to /sys fs somewhere?
        if (ret)
        {
            // gpio_request failed with error -517 // currently, but I have not vetted if 4 is appropriate for RPI
            pr_err("DHT22: gpio_request failed with error %d\n", ret);
            return ret;
        }
        // PRN need to export/unexport? would it help to do this to test via sysfs debug fs (IIUC that makes this possible)... also wondering if setting label with request + export then results in that label showing in the output of the command `gpioinfo`? (instead of "unused")... note unused seems to be a column for a second label of sorts which I speculate is from when it is exported? and first requested? or?
    }

    // Register the character device
    major = register_chrdev(0, "dht22", &dht22_fops);
    if (major < 0)
    {
        pr_err("DHT22: Unable to register character device\n");
        gpio_free(USE_GLOBAL_LINE_NUMBER);
        return major;
    }

    // Create the device class
    dht22_class = class_create("dht22");
    if (IS_ERR(dht22_class))
    {
        unregister_chrdev(major, "dht22");
        pr_err("DHT22: Failed to create class\n");
        if (do_request_gpio)
            gpio_free(USE_GLOBAL_LINE_NUMBER);
        return PTR_ERR(dht22_class);
    }

    // Create the device file /dev/dht22
    dht22_device = device_create(dht22_class, NULL, MKDEV(major, 0), NULL, "dht22");
    if (IS_ERR(dht22_device))
    {
        class_destroy(dht22_class);
        unregister_chrdev(major, "dht22");
        pr_err("DHT22: Failed to create device\n");
        if (do_request_gpio)
            gpio_free(USE_GLOBAL_LINE_NUMBER);
        return PTR_ERR(dht22_device);
    }

    pr_info("DHT22: Driver loaded successfully, /dev/dht22 created\n");
    return 0;
}

static void __exit dht22_exit(void)
{
    // Free the GPIO pin
    if (do_request_gpio)
        gpio_free(USE_GLOBAL_LINE_NUMBER);

    // Remove the device
    device_destroy(dht22_class, MKDEV(major, 0));

    // Destroy the device class
    class_destroy(dht22_class);

    // Unregister the character device
    unregister_chrdev(major, "dht22");

    pr_info("DHT22: Driver unloaded\n");
}

module_init(dht22_init);
module_exit(dht22_exit);

MODULE_LICENSE("GPL"); // IF incompatible with other used modules, then compile fails! i.e. MIT here fails compile!
MODULE_AUTHOR("Wes");
MODULE_DESCRIPTION("/dev_num/dht22 driver");
MODULE_VERSION("0.1");
