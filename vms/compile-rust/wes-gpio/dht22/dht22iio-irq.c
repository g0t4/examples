#include <linux/iio/iio.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/mod_devicetable.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/device.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>
#include <linux/gpio.h>
#include <linux/delay.h>
#include <linux/interrupt.h>
#include <linux/platform_device.h>
#include "../ledfs/pins.h"

#define DEBUG_DHT22
#ifdef DEBUG_DHT22
// TODO are logs prefixed with DRIVER_NAME or MODULE_NAME? also cleanup format strings below that prepend DHT22: ...
#define PR_INFO(fmt, ...) pr_info(fmt, ##__VA_ARGS__)
// #define PR_INFO(fmt, ...) pr_info(DRIVER_NAME ": " fmt, ##__VA_ARGS__) // TODO ???
#define PR_ERR(fmt, ...) pr_err(fmt, ##__VA_ARGS__)
// #define PR_ERR(fmt, ...) pr_err(DRIVER_NAME ": " fmt, ##__VA_ARGS__) // TODO ???
#else
#define PR_INFO(fmt, ...)
#define PR_ERR(fmt, ...)
#endif

#define GPIO_DATA_LINE RPI5_GPIO_4 // works well, FYI does not conflict with pins used by sense-hat

#define TIMEOUT_US 1000000 // 1 second

struct dht22
{
	struct iio_dev *indio_dev;
	struct device *dev;
	struct gpio_desc *gpio_desc;
	int irq;

	int celsius_tenths;
	int humidity_tenths;
	int fahrenheit_tenths;
	int last_read_jiffies;
};

// IIO overview: https://wiki.analog.com/software/linux/docs/iio/iio
// use iio-tri-sysfs to trigger sample aquisition https://wiki.analog.com/software/linux/docs/iio/iio-trig-sysfs
//    use this to combine triggering and ring buffer (in software):
//      iio_triggered_buffer_setup_ext
//        takes iio_dev => makes iio_buffer

// kernel docs for GPIO => entrypoint explains legacy vs current (gpiod) APIs
// https://github.com/raspberrypi/linux/blob/rpi-6.8.y/Documentation/driver-api/gpio/intro.rst#L8
// legacy absolute GPIO numbering API => https://github.com/raspberrypi/linux/blob/rpi-6.8.y/Documentation/driver-api/gpio/legacy.rst#L1

// wait_for_edge_to_or_timeout
static bool wait_for_edge_to(int expected_value, struct gpio_desc *desc)
{
	ktime_t start_time = ktime_get();
	while (gpiod_get_raw_value(desc) != expected_value)
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

static int dht22_read(struct dht22 *dht22)
{
	// !! TODO port my 39 bit failure logic from python to C too (this is only other thing that really matters)

	// FYI protocol http://www.ocfreaks.com/basics-interfacing-dht11-dht22-humidity-temperature-sensor-mcu/
	// http://www.ocfreaks.com/imgs/embedded/dht/dhtxx_protocol.png

	int data[5] = {0}; // 5 bytes (8 bits) of data (humidity and temperature) => can use short instead of int
	// TODO build array of text messages to log for debugging, like in my python code
	int byte_index, bit_index;
	PR_INFO("DHT22: Reading data\n");

	// FYI gpio_desc ... now comes via device tree => platform device => iio device

	// FYI gpio_desc => https://github.com/raspberrypi/linux/blob/rpi-6.8.y/drivers/gpio/gpiolib.h#L157-L187

	// Send the start signal to DHT22
	gpiod_direction_output(dht22->gpio_desc, 0); // pull low signals to send reading
	udelay(400);																 // much more reliable with my current sensors, though sensor2 needs 480us to start working and ECC for 39th bith most of the time
	gpiod_direction_output(dht22->gpio_desc, 1); // release (pulls high b/c of pull-up resistor too)
	// no delays, just go right to waiting for the sensor to respond, if I add delay I tend to miss first bit on my good sensor1 at least

	gpiod_direction_input(dht22->gpio_desc); // start reading right away, wait for sensor to pull low indicating it is ready to send data

	if (!wait_for_edge_to(0, dht22->gpio_desc))
	{
		PR_ERR("DHT22: Timeout - sensor didn't respond with initial low signal\n");
		return -ETIMEDOUT;
	}
	PR_INFO("DHT22: Sensor response low\n");

	if (!wait_for_edge_to(1, dht22->gpio_desc))
	{
		PR_ERR("DHT22: Timeout - sensor didn't pull the line high (after initial low)\n");
		return -ETIMEDOUT;
	}
	PR_INFO("DHT22: Sensor response high\n");

	if (!wait_for_edge_to(0, dht22->gpio_desc))
	{
		PR_ERR("DHT22: Timeout - sensor didn't pull the line low for first byte \n");
		return -ETIMEDOUT;
	}

	// Read the data (40 bits)
	for (byte_index = 0; byte_index < 5; byte_index++)
	{
		for (bit_index = 0; bit_index < 8; bit_index++)
		{
			if (!wait_for_edge_to(1, dht22->gpio_desc))
			{
				PR_ERR("DHT22: Timeout (bit: %d) - sensor didn't pull the line high for bit start\n", byte_index * 8 + bit_index);
				return -ETIMEDOUT;
			}
			int start = ktime_get();

			if (!wait_for_edge_to(0, dht22->gpio_desc))
			{
				PR_ERR("DHT22: Timeout (bit: %d) - sensor didn't pull the line low for bit end\n", byte_index * 8 + bit_index);
				return -ETIMEDOUT;
			}
			int end = ktime_get();
			int duration = ktime_us_delta(end, start);
			PR_INFO("DHT22: Bit (bit: %d) duration: %d\n", byte_index * 8 + bit_index, duration);

			data[byte_index] <<= 1; // shift left to make room for new bit
			if (duration > 40)			// 26-28us for '0', 70us for '1'
			{
				data[byte_index] |= 1; // set last bit to 1
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
		PR_ERR("DHT22: Data checksum error\n");
		return -EBADMSG;
	}

	// SENSOR returns TENTHS (/10 for value)... keep in tenths so I can show decimal place easily in format strings
	dht22->humidity_tenths = ((data[0] << 8) + data[1]);
	dht22->celsius_tenths = (((data[2] & 0x7F) << 8) + data[3]);
	if (data[2] & 0x80)
	{
		dht22->celsius_tenths = -dht22->celsius_tenths; // Handle negative temperature
	}
	dht22->fahrenheit_tenths = (dht22->celsius_tenths * 9 / 5) + 320;

	return 0;
}

static int read_raw(struct iio_dev *iio_dev,
										struct iio_chan_spec const *chan,
										int *val,
										int *val2,
										long mask)
{
	PR_INFO("read_raw channel %d\n", chan->type);

	struct dht22 *dht22 = iio_priv(iio_dev); // IIO interface, so if you want other device info, have to look it up

	int ms_since_last_read = jiffies_to_msecs(jiffies - dht22->last_read_jiffies);
	if (ms_since_last_read < 2000 && ms_since_last_read > 0)
	{
		PR_INFO("read_raw: returning cached data\n");
		// PRN consolidate with logic below to return data
		if (chan->type == IIO_TEMP)
			*val = dht22->celsius_tenths; // value is integer instead of string/buffer like I did with dht22fs, much nicer!
		else if (chan->type == IIO_HUMIDITYRELATIVE)
			*val = dht22->humidity_tenths;
		else
			return -EINVAL;

		return IIO_VAL_INT; // report back its an integer?
	}
	PR_INFO("read_raw: Data is stale, reading new data\n");

	// mutex_lock(&dht11->lock); // TODO

	int ret = dht22_read(dht22);
	if (ret != 0)
	{
		return -EIO;
	}
	dht22->last_read_jiffies = jiffies; // start counter AFTER successful read, ms precision is good enough for what I am doing so jiffies is fine (don't need ktime_get which is ns precision)

	// mutex_unlock(&dht11->lock); // TODO (also goto err: ... like dht11 does)

	// PRN use val as integer and val2 as decimal? dht11 doesn't do this
	if (chan->type == IIO_TEMP)
		*val = dht22->celsius_tenths; // value is integer instead of string/buffer like I did with dht22fs, much nicer!
	else if (chan->type == IIO_HUMIDITYRELATIVE)
		*val = dht22->humidity_tenths;
	else
		return -EINVAL;

	PR_INFO("DHT22: channel %d, value: %d\n", chan->type, *val);
	return IIO_VAL_INT;
}

static const struct iio_info dht22_iio_info = {
		.read_raw = read_raw,
};

// each channel => /sys/bus/iio/devices/iio:deviceX/in_<type>_raw
static const struct iio_chan_spec dht22_chan_spec[] = {
		{
				.type = IIO_TEMP,
				.info_mask_separate = BIT(IIO_CHAN_INFO_PROCESSED),
		},
		{
				.type = IIO_HUMIDITYRELATIVE,
				.info_mask_separate = BIT(IIO_CHAN_INFO_PROCESSED),
		}};

static int dht22_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct dht22 *dht22;
	struct iio_dev *iio;

	iio = devm_iio_device_alloc(dev, sizeof(*dht22)); // also links dht22 to iio device, can retrieve later on in read (above)
	if (!iio)
	{
		dev_err(dev, "Failed to allocate IIO device\n");
		return -ENOMEM;
	}

	dht22 = iio_priv(iio);																	// retrieve allocated memory for private data (dht22) from call to devm_iio_device_alloc (above)
	dht22->dev = dev;																				// store platform device pointer
	dht22->gpio_desc = devm_gpiod_get(dev, NULL, GPIOD_IN); // get GPIO descriptor from device tree (i.e. /boot/firmware/config.txt on rpi)
	if (IS_ERR(dht22->gpio_desc))
		return PTR_ERR(dht22->gpio_desc);

	// TODO rewrite to be IRQ triggered later on (after port to IIO)
	// dht22->irq = gpiod_to_irq(dht22->gpio_desc);
	// if (dht22->irq < 0) {
	//   dev_err(dev, "GPIO %d has no interrupt\n", desc_to_gpio(dht22->gpio_desc));
	//   return -EINVAL;
	// }

	// TODO, I don't think this is needed:
	// platform_set_drvdata(pdev, iio);

	// init_completion(&dht22->completion); //
	// mutex_init(&dht22->lock); // TODO lock on read (one at a time)
	iio->name = pdev->name;
	iio->info = &dht22_iio_info;
	iio->modes = INDIO_DIRECT_MODE;
	iio->channels = dht22_chan_spec;
	iio->num_channels = ARRAY_SIZE(dht22_chan_spec);

	return devm_iio_device_register(dev, iio); // link lifetime of iio device to platform device, thus when platform device is removed, iio device is removed (freeing resources of both)
}

static const struct of_device_id dht22_dt_ids[] = {
		{
				.compatible = "dht22iio-irq",
		},
		{}};
MODULE_DEVICE_TABLE(of, dht22_dt_ids);

#define DRIVER_NAME "dht22iio-irq"

static struct platform_driver dht22_driver = {
		.driver = {
				.name = DRIVER_NAME,
				.of_match_table = dht22_dt_ids,
		},
		.probe = dht22_probe,
};

module_platform_driver(dht22_driver); // instead of module_init and module_exit, for simple drivers
// __init/__exit via this macro =>  https://github.com/raspberrypi/linux/blob/rpi-6.8.y/include/linux/device/driver.h#L257-L268

MODULE_LICENSE("GPL"); // IF incompatible with other used modules, then compile fails! i.e. MIT here fails compile!
MODULE_AUTHOR("Wes Higbee");
MODULE_DESCRIPTION("dht22iio-irq driver");
MODULE_VERSION("0.1");
