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

static int dht22_read(void)
{
    // TODO lock for one read at a time?
    // TODO fail if read too soon after last read? (IIUC 2 second probing interval minimum required)

    // FYI protocol http://www.ocfreaks.com/basics-interfacing-dht11-dht22-humidity-temperature-sensor-mcu/
    // http://www.ocfreaks.com/imgs/embedded/dht/dhtxx_protocol.png

    int data[5] = {0}; // 5 bytes (8 bits) of data (humidity and temperature) => can use short instead of int
    // TODO build array of text messages to log for debugging, like in my python code
    int i, j;
    pr_info("DHT22: Reading data\n");

    // Send the start signal to DHT22
    gpio_direction_output(GPIO_DATA_LINE, 0); // pull low signals to send reading
    udelay(400);                              // much more reliable with my current sensors, though sensor2 needs 480us to start working and ECC for 39th bith most of the time
    gpio_direction_output(GPIO_DATA_LINE, 1); // release (pulls high b/c of pull-up resistor too)
    // no delays, just go right to waiting for the sensor to respond, if I add delay I tend to miss first bit on my good sensor1 at least

    gpio_direction_input(GPIO_DATA_LINE);       // start reading right away, wait for sensor to pull low indicating it is ready to send data
    while (gpio_get_value(GPIO_DATA_LINE) == 1) // while still high (waiting for sensor to pull low)
        ;
    pr_info("DHT22: Sensor response low\n");
    while (gpio_get_value(GPIO_DATA_LINE) == 0) // while still low (waiting for sensor to pull high)
        ;
    pr_info("DHT22: Sensor response high\n");
    while (gpio_get_value(GPIO_DATA_LINE) == 1) // while still high (waiting for sensor to pull low to start first bit)
        ;

    // Read the data (40 bits) // each bit is 50us low, then high for ... 26-28us => "0", 70us => "1"
    // up to 5ms total if all 1s, ~3ms if all 0s
    for (i = 0; i < 5; i++)
    {
        // 5 bytes of data sent
        for (j = 0; j < 8; j++)
        {
            // 8 bits per byte obviously
            while (gpio_get_value(GPIO_DATA_LINE) == 0) // while still low (start of bit)
                ;                                       // Wait for the pin to go high, during this time we are in the 50us low start of bit state
            int start = ktime_get();
            pr_info("DHT22: Bit start high\n");
            while (gpio_get_value(GPIO_DATA_LINE) == 1) // while still high (end of bit)
                ;                                       // Wait for the pin to go low, during this time we are in the 26-28us high state for '0' or 70us high state for '1'
            int end = ktime_get();
            int duration = ktime_us_delta(end, start);
            pr_info("DHT22: Bit duration: %d\n", duration);
            data[i] <<= 1;     // shift left to make room for new bit
            if (duration > 40) // 26-28us for '0', 70us for '1'
            {
                data[i] |= 1; // set last bit to 1
            }
            // else 0, already 0 after left shift by 1
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

static int __init dht22_init(void)
{
    major = register_chrdev(0, "dht22", &dht22_fops);
    if (major < 0)
    {
        pr_err("DHT22: Unable to register character device\n");
        gpio_free(GPIO_DATA_LINE);
        return major;
    }

    // Create the device class
    dht22_class = class_create("dht22");
    if (IS_ERR(dht22_class))
    {
        unregister_chrdev(major, "dht22");
        pr_err("DHT22: Failed to create class\n");
        return PTR_ERR(dht22_class);
    }

    // Create the device file /dev/dht22
    dht22_device = device_create(dht22_class, NULL, MKDEV(major, 0), NULL, "dht22");
    if (IS_ERR(dht22_device))
    {
        class_destroy(dht22_class);
        unregister_chrdev(major, "dht22");
        pr_err("DHT22: Failed to create device\n");
        return PTR_ERR(dht22_device);
    }

    pr_info("DHT22: Driver loaded successfully, /dev/dht22 created\n");
    return 0;
}

static void __exit dht22_exit(void)
{
    // Remove the device
    device_destroy(dht22_class, MKDEV(major, 0));

    // Destroy the device class
    class_destroy(dht22_class);

    unregister_chrdev(major, "dht22");

    pr_info("DHT22: Driver unloaded\n");
}

module_init(dht22_init);
module_exit(dht22_exit);

MODULE_LICENSE("GPL"); // IF incompatible with other used modules, then compile fails! i.e. MIT here fails compile!
MODULE_AUTHOR("Wes");
MODULE_DESCRIPTION("/dev_num/dht22 driver");
MODULE_VERSION("0.1");
