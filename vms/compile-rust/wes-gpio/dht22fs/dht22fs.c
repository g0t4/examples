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

#define DEBUG_DHT22
#ifdef DEBUG_DHT22
#define PR_INFO(fmt, ...) pr_info(fmt, ##__VA_ARGS__)
#define PR_ERR(fmt, ...) pr_err(fmt, ##__VA_ARGS__)
#else
#define PR_INFO(fmt, ...)
#define PR_ERR(fmt, ...)
#endif

#define GPIO_DATA_LINE RPI5_GPIO_17 // TODO what pin?
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

// PRN times array for history, so I can dump if smth goes wrong but not otherwise
// #define MAX_ENTRIES 200
// #define MAX_LENGTH 200
// static char times[MAX_ENTRIES][MAX_LENGTH];

#define TIMEOUT_US 1000000 // 1 second

static bool wait_for_edge_to(int expected_value)
{
    ktime_t start_time = ktime_get();
    while (gpio_get_value(GPIO_DATA_LINE) != expected_value)
    {
        if (ktime_us_delta(ktime_get(), start_time) > TIMEOUT_US)
        {
            return false;
        }
    }

    // add back , const char *label PARAM if:
    // int total_us = ktime_us_delta(ktime_get(), start_time);
    // PR_INFO("%s: %dus (%d)\n", label, total_us, expected_value); // PRN add to times array like in python

    return true;
}

static int dht22_read(void)
{
    // !! TODO port my 39 bit failure logic from python to C too (this is only other thing that really matters)

    // FYI protocol http://www.ocfreaks.com/basics-interfacing-dht11-dht22-humidity-temperature-sensor-mcu/
    // http://www.ocfreaks.com/imgs/embedded/dht/dhtxx_protocol.png

    int data[5] = {0}; // 5 bytes (8 bits) of data (humidity and temperature) => can use short instead of int
    // TODO build array of text messages to log for debugging, like in my python code
    int byte_index, bit_index;
    PR_INFO("DHT22: Reading data\n");

    // Send the start signal to DHT22
    gpio_direction_output(GPIO_DATA_LINE, 0); // pull low signals to send reading
    udelay(400);                              // much more reliable with my current sensors, though sensor2 needs 480us to start working and ECC for 39th bith most of the time
    gpio_direction_output(GPIO_DATA_LINE, 1); // release (pulls high b/c of pull-up resistor too)
    // no delays, just go right to waiting for the sensor to respond, if I add delay I tend to miss first bit on my good sensor1 at least

    gpio_direction_input(GPIO_DATA_LINE); // start reading right away, wait for sensor to pull low indicating it is ready to send data

    if (!wait_for_edge_to(0))
    {
        PR_ERR("DHT22: Timeout - sensor didn't respond with initial low signal\n");
        return -1;
    }
    PR_INFO("DHT22: Sensor response low\n");

    if (!wait_for_edge_to(1))
    {
        PR_ERR("DHT22: Timeout - sensor didn't pull the line high (after initial low)\n");
        return -1;
    }
    PR_INFO("DHT22: Sensor response high\n");

    if (!wait_for_edge_to(0))
    {
        PR_ERR("DHT22: Timeout - sensor didn't pull the line low for first byte \n");
        return -1;
    }

    // Read the data (40 bits)
    for (byte_index = 0; byte_index < 5; byte_index++)
    {
        for (bit_index = 0; bit_index < 8; bit_index++)
        {
            if (!wait_for_edge_to(1))
            {
                PR_ERR("DHT22: Timeout (bit: %d) - sensor didn't pull the line high for bit start\n", byte_index * 8 + bit_index);
                return -1;
            }
            int start = ktime_get();

            if (!wait_for_edge_to(0))
            {
                PR_ERR("DHT22: Timeout (bit: %d) - sensor didn't pull the line low for bit end\n", byte_index * 8 + bit_index);
                return -1;
            }
            int end = ktime_get();
            int duration = ktime_us_delta(end, start);
            PR_INFO("DHT22: Bit (bit: %d) duration: %d\n", byte_index * 8 + bit_index, duration);

            data[byte_index] <<= 1; // shift left to make room for new bit
            if (duration > 40)      // 26-28us for '0', 70us for '1'
            {
                data[byte_index] |= 1; // set last bit to 1
            }
            // else 0, already 0 after left shift by 1
            // FUCK YEAH THIS JUST WORKED!!!!!!!! though my file cat operation is hanging... Temperature: 24 C, Humidity: 70 % ... humidity seems high but temp is accurate
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
        PR_ERR("DHT22: Data checksum error\n");
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

static int last_read_jiffies = 0;

static ssize_t dht22_read_data(struct file *file, char __user *buf, size_t len, loff_t *offset)
{
    PR_INFO("read_data: len: %d, offset: %lld\n", (int)len, *offset);
    char buffer[64];
    if (*offset > 0)
    {
        PR_INFO("read_data: EOF, all data returned in single read\n");
        return 0; // Indicate EOF to stop further reading
    }

    int ms_since_last_read = jiffies_to_msecs(jiffies - last_read_jiffies);
    // handle negative for wrap around
    if (ms_since_last_read < 2000 && ms_since_last_read > 0)
    {
        PR_INFO("read_data: Data is fresh, returning cached data\n");
        snprintf(buffer, sizeof(buffer), "Cached Data: Humidity: %d %%, Temperature: %d C (%d F)\n", sensor_data.humidity, sensor_data.temperature, (sensor_data.temperature * 9 / 5) + 32);
        return simple_read_from_buffer(buf, len, offset, buffer, strlen(buffer));
    }
    PR_INFO("read_data: Data is stale, reading new data\n");

    // TODO add locking for first request to read, block subsequent calls before data read first time... and fulfill them with the cached data
    if (dht22_read() < 0)
    {
        return -EIO; // general IO error,
        // FYI cat responds with "Bad address" if I return -EFAULT... not so useful
    }
    last_read_jiffies = jiffies; // start counter AFTER successful read, ms precision is good enough for what I am doing so jiffies is fine (don't need ktime_get which is ns precision)

    snprintf(buffer, sizeof(buffer), "Humidity: %d %%, Temperature: %d C (%d F)\n", sensor_data.humidity, sensor_data.temperature, (sensor_data.temperature * 9 / 5) + 32);

#ifdef DEBUG_DHT22
    int buffer_len = strlen(buffer); // if I inline this, I get warnings about format
    PR_INFO("strlen(buffer): %d\n", buffer_len);
#endif

    PR_INFO("DHT22: %s\n", buffer);
    return simple_read_from_buffer(buf, len, offset, buffer, strlen(buffer));
}

static const struct file_operations dht22_fops = {
    .owner = THIS_MODULE,
    .read = dht22_read_data,
};

static int major;
static struct class *dht22_class = NULL;
static struct device *dht22_device = NULL;

static int __init dht22_init(void)
{
    major = register_chrdev(0, "dht22", &dht22_fops);
    if (major < 0)
    {
        PR_ERR("DHT22: Unable to register character device\n");
        gpio_free(GPIO_DATA_LINE);
        return major;
    }

    // Create the device class
    dht22_class = class_create("dht22");
    if (IS_ERR(dht22_class))
    {
        unregister_chrdev(major, "dht22");
        PR_ERR("DHT22: Failed to create class\n");
        return PTR_ERR(dht22_class);
    }

    // Create the device file /dev/dht22
    dht22_device = device_create(dht22_class, NULL, MKDEV(major, 0), NULL, "dht22");
    if (IS_ERR(dht22_device))
    {
        class_destroy(dht22_class);
        unregister_chrdev(major, "dht22");
        PR_ERR("DHT22: Failed to create device\n");
        return PTR_ERR(dht22_device);
    }

    PR_INFO("DHT22: Driver loaded successfully, /dev/dht22 created\n");
    return 0;
}

static void __exit dht22_exit(void)
{
    // Remove the device
    device_destroy(dht22_class, MKDEV(major, 0));

    // Destroy the device class
    class_destroy(dht22_class);

    unregister_chrdev(major, "dht22");

    PR_INFO("DHT22: Driver unloaded\n");
}

module_init(dht22_init);
module_exit(dht22_exit);

MODULE_LICENSE("GPL"); // IF incompatible with other used modules, then compile fails! i.e. MIT here fails compile!
MODULE_AUTHOR("Wes");
MODULE_DESCRIPTION("/dev_num/dht22 driver");
MODULE_VERSION("0.1");
