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

struct dht22_data
{
    int temperature;
    int humidity;
};

static struct dht22_data sensor_data;

static int dht22_read(void)
{
    int data[5] = {0}; // 5 bytes of data (humidity and temperature)
    int i, j;

    // Send the start signal to DHT22
    gpio_direction_output(DHT22_GPIO_PIN, 1); // pull high
    udelay(20);                               // for 20us
    gpio_direction_output(DHT22_GPIO_PIN, 0); // pull low
    msleep(18);                               // for at least 18ms
    gpio_direction_output(DHT22_GPIO_PIN, 1); // pull high
    udelay(40);                               // for 40us
    gpio_direction_input(DHT22_GPIO_PIN);

    // Wait for the sensor response (80us low, 80us high)
    while (gpio_get_value(DHT22_GPIO_PIN) == 1)
        ;
    udelay(80);
    while (gpio_get_value(DHT22_GPIO_PIN) == 0)
        ;
    udelay(80);

    // Read the data (40 bits)
    for (i = 0; i < 5; i++)
    {
        for (j = 0; j < 8; j++)
        {
            while (gpio_get_value(DHT22_GPIO_PIN) == 0)
                ;       // Wait for the pin to go high
            udelay(30); // Delay to determine if it's a '1' or '0'

            if (gpio_get_value(DHT22_GPIO_PIN) == 1)
            {
                data[i] |= (1 << (7 - j)); // Set bit
                while (gpio_get_value(DHT22_GPIO_PIN) == 1)
                    ; // Wait for the pin to go low
            }
        }
    }

    // Check if data is valid
    if (data[4] != ((data[0] + data[1] + data[2] + data[3]) & 0xFF))
    {
        pr_err("DHT22: Data checksum error\n");
        return -1;
    }

    // Convert data to temperature and humidity
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

static int __init dht22_init(void)
{

    int ret = gpio_request(DHT22_GPIO_PIN, "dht22_pin");
    if (ret)
    {
        pr_err("DHT22: Unable to request GPIO pin\n");
        return ret;
    }

    ret = register_chrdev(0, "dht22", &dht22_fops);
    if (ret < 0)
    {
        pr_err("DHT22: Unable to register character device\n");
        gpio_free(DHT22_GPIO_PIN);
        return ret;
    }

    pr_info("DHT22: Driver loaded successfully\n");
    return 0;
}

static void __exit dht22_exit(void)
{
    // Free the GPIO pin
    gpio_free(DHT22_GPIO_PIN);

    // Unregister the character device
    unregister_chrdev(0, "dht22");

    pr_info("DHT22: Driver unloaded\n");
}

module_init(dht22_init);
module_exit(dht22_exit);

MODULE_LICENSE("GPL"); // IF incompatible with other used modules, then compile fails! i.e. MIT here fails compile!
MODULE_AUTHOR("Wes");
MODULE_DESCRIPTION("/dev_num/dht22 driver");
MODULE_VERSION("0.1");
