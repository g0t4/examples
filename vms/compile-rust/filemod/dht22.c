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

#define DHT22_GPIO_PIN 4 // TODO find CORRECT PIN ON RPI

static int major;

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
    gpio_direction_output(DHT22_GPIO_PIN, 1); // pull high
    udelay(20);                               // for 20us (not sure this needs to be 20us? protocol says pull low for 18us to start?) // TODO does it need to be 20us?
    gpio_direction_output(DHT22_GPIO_PIN, 0); // pull low
    msleep(18);                               // for at least 18ms
    gpio_direction_output(DHT22_GPIO_PIN, 1); // pull high
    udelay(40);                               // for 40us (FYI response can come after 20-40us so I guess wait 40us to be safe)

    gpio_direction_input(DHT22_GPIO_PIN); // start reading (can't I start reading right after pull high? or?)

    // Wait for the sensor response (80us low, 80us high)
    while (gpio_get_value(DHT22_GPIO_PIN) == 1)
        ;
    udelay(80); // once low, wait 80us // should we check every 5us instead of just skip 80?!
    while (gpio_get_value(DHT22_GPIO_PIN) == 0)
        ;
    udelay(80); // once high, wait 80us => "get ready" for data transmission

    // Read the data (40 bits) // each bit is 50us low, then high for ... 26-28us => "0", 70us => "1"
    for (i = 0; i < 5; i++)
    {
        // 5 bytes of data sent
        for (j = 0; j < 8; j++)
        {
            // 8 bits per byte obviously
            while (gpio_get_value(DHT22_GPIO_PIN) == 0)
                ;       // Wait for the pin to go high, during this time we are in the 50us low start of bit state
            udelay(30); // Delay to determine if it's a '1' or '0'
            // after 30us if it is still high, then it is a '1', otherwise it is a '0'
            if (gpio_get_value(DHT22_GPIO_PIN) == 1)
            {
                data[i] |= (1 << (7 - j)); // Set bit
                while (gpio_get_value(DHT22_GPIO_PIN) == 1)
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

static struct class *dht22_class = NULL;
static struct device *dht22_device = NULL;

static int __init dht22_init(void)
{

    // int ret = gpio_request(DHT22_GPIO_PIN, "dht22_pin");
    // if (ret)
    // {
    //     pr_err("DHT22: Unable to request GPIO pin\n");
    //     return ret;
    // }
    // Register the character device

    major = register_chrdev(0, "dht22", &dht22_fops);
    if (major < 0) {
        pr_err("DHT22: Unable to register character device\n");
        // gpio_free(DHT22_GPIO_PIN);
        return major;
    }

    // Create the device class
    dht22_class = class_create("dht22");
    if (IS_ERR(dht22_class)) {
        unregister_chrdev(major, "dht22");
        pr_err("DHT22: Failed to create class\n");
        // gpio_free(DHT22_GPIO_PIN);
        return PTR_ERR(dht22_class);
    }

    // Create the device file /dev/dht22
    dht22_device = device_create(dht22_class, NULL, MKDEV(major, 0), NULL, "dht22");
    if (IS_ERR(dht22_device)) {
        class_destroy(dht22_class);
        unregister_chrdev(major, "dht22");
        pr_err("DHT22: Failed to create device\n");
        // gpio_free(DHT22_GPIO_PIN);
        return PTR_ERR(dht22_device);
    }

    pr_info("DHT22: Driver loaded successfully, /dev/dht22 created\n");
    return 0;
}

static void __exit dht22_exit(void)
{
    // Free the GPIO pin
    //gpio_free(DHT22_GPIO_PIN);

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
