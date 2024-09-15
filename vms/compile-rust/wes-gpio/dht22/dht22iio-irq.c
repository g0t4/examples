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

#define DRIVER_NAME "dht22iio-irq"

#define TIMEOUT_US 1000000								// 1 second
#define NUM_EDGES_PER_SAMPLE (41 * 2 + 1) //  83 total edges (2 unique edges per bit, start bit too, and then initial drop low at start... bit has low and high periods, so initial drop to low is the 1 extra before low/high preamble bit, low/high bit 1, low/high bit 2, etc
// 41 bits total with preamble bit and we also have extra edge to drop low before preamble bit
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

	struct completion completion;

	struct mutex lock;

	int last_level;												// TODO - 0 or 1 for VALIDATING edges aren't missed... THIS IS ICING ON CAKE, SKIP FOR NOW?
	u64 edge_times_ns[NUM_EDGES_PER_SAMPLE + 10]; // 10 is a safe buffer for now // TODO REMOVE EXTRA when mostly done

	int num_edges;
};

// IIO overview: https://wiki.analog.com/software/linux/docs/iio/iio
// use iio-tri-sysfs to trigger sample aquisition https://wiki.analog.com/software/linux/docs/iio/iio-trig-sysfs
//    use this to combine triggering and ring buffer (in software):
//      iio_triggered_buffer_setup_ext
//        takes iio_dev => makes iio_buffer

// kernel docs for GPIO => entrypoint explains legacy vs current (gpiod) APIs
// https://github.com/raspberrypi/linux/blob/rpi-6.8.y/Documentation/driver-api/gpio/intro.rst#L8
// legacy absolute GPIO numbering API => https://github.com/raspberrypi/linux/blob/rpi-6.8.y/Documentation/driver-api/gpio/legacy.rst#L1

/*
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
*/

static irqreturn_t dht22_handle_irq(int irq, void *dev_id)
{
	// struct iio_dev *iio = data;
	// struct dht11 *dht11 = iio_priv(iio);

	struct dht22 *dht22 = dev_id;

	int current_value = gpiod_get_value(dht22->gpio_desc);
	u64 time = ktime_get_boottime_ns(); // TODO is this safe to use for time? could it wrap?  would lose a reading..NBD really but could likely be avoided
	int time_us = time / 1000;

	int current_bit = (dht22->num_edges - 3) / 2; // so bit 0 == edges 3&4, bit 1 == edges 5&6, etc
	// bit 0 == first data bit, bit -1 == sensor preamble bit, bit -2 == host preamble bit
	// TODO make sure bit definition here matches to below just to avoid confusing myself when looking at logs
	PR_INFO("  DHT22: bit:%d, edge: %d, value: %d, time: %d us\n", current_bit, dht22->num_edges, current_value, time_us);
	if (dht22->last_level == current_value)
	{
		// warning for now to see if it even occurs, I don't think dht11 driver tracked this at all
		PR_INFO("DHT22: last_level=%d == current_value=%d\n", dht22->last_level, current_value);
	}
	dht22->last_level = current_value;

	dht22->edge_times_ns[dht22->num_edges] = time;

	dht22->num_edges++;

	// if exceed stop condition, then stop with completion
	if (dht22->num_edges >= NUM_EDGES_PER_SAMPLE) // TODO WRONG... // 2 (low/high response) + 40*2 bits + final release (high)
		complete(&dht22->completion);

	return IRQ_HANDLED;
}

#define HIGH_THRESHOLD_NS 40000 // 40us

static int dht22_read(struct dht22 *dht22)
{
	PR_INFO("DHT22: Reading data\n");
	// ! safe to assume only one reader here... b/c I have code setup for mutex in read_raw (below)

	// TODO check ambiguous resolution of sensor data (see dht11 code)

	// tell sensor to start sending data
	int ret = gpiod_direction_output(dht22->gpio_desc, 0); // pull low signals to send reading
	if (ret)
	{
		PR_ERR("DHT22: Failed to set GPIO direction and pull low\n");
		return ret;
	}
	// TODO 18000 works here... does 400 still work?! can also do 1ms as that was suggested to be ok too... how did this matter for my polling driver?!
	udelay(18000);																		 // much more reliable with my current sensors, though sensor2 needs 480us to start working and ECC for 39th bith most of the time
	ret = gpiod_direction_output(dht22->gpio_desc, 1); // release (pulls high b/c of pull-up resistor too)
	if (ret)
	{
		PR_ERR("DHT22: Failed to set GPIO direction and release (pull high)\n");
		return ret;
	}
	dht22->last_level = 1; // was high, will be pulled low next by sensor
	dht22->num_edges = 0;
	ret = gpiod_direction_input(dht22->gpio_desc);
	if (ret)
	{
		PR_ERR("DHT22: Failed to set GPIO direction to input after my preamble\n");
		return ret;
	}

	// sensor pulls low here to respond that it is ready and then it releases and then sends first bit (low 50ms, low/high ~28us, high ~70us (use >40us))

	// immediately register irq after releasing line
	ret = devm_request_irq(dht22->dev, dht22->irq, dht22_handle_irq,
												 IRQF_TRIGGER_RISING | IRQF_TRIGGER_FALLING,
												 DRIVER_NAME, dht22); // devm also lets me pass my custom struct for last arg, whereas IIUC request_irq requires it be iio_dev?
	if (ret)
	{
		PR_ERR("DHT22: Failed to request IRQ %d\n", dht22->irq);
		return ret;
	}

	reinit_completion(&dht22->completion); // this spot s/b fine so its used next:

	// wait for all data to be sent (or timeout)
	wait_for_completion_killable_timeout(&dht22->completion, usecs_to_jiffies(TIMEOUT_US));

	// stop irq handler:
	devm_free_irq(dht22->dev, dht22->irq, dht22);

	if (dht22->num_edges < NUM_EDGES_PER_SAMPLE) // TODO this is wrong...
	{
		PR_ERR("DHT22: num_edges < %d: actual=%d\n", NUM_EDGES_PER_SAMPLE, dht22->num_edges);
		return -ETIMEDOUT;
	}

	int data[5] = {0}; // 5 bytes (8 bits) of data (humidity and temperature) => can use short instead of int
	int byte_index, bit_index;
	for (byte_index = 0; byte_index < 5; byte_index++)
	{
		int this_byte = 0; // FYI I could use data[x] along the way below but this is more readable IMO
		for (bit_index = 0; bit_index < 8; bit_index++)
		{
			// skip first two edges... skip edge low and go for edge high (literally #3)
			int bit_num = byte_index * 8 + bit_index;
			int up_edge_num = (bit_num + 1) * 2 + 1; // add start bit
			int down_edge_num = up_edge_num + 1;
			u64 up_time_ns = dht22->edge_times_ns[up_edge_num];
			u64 down_time_ns = dht22->edge_times_ns[down_edge_num];
			// FYI this is the time from low->high (up) and high->low (down) only... ignoring initial low period
			u64 diff_ns = down_time_ns - up_time_ns;
			int diff_us = diff_ns / 1000;
			PR_INFO("DHT22: Bit (bit: %d) duration: %d us\n", bit_num, diff_us);
			if (diff_ns < 0)
			{
				// only would happen if irqs out of order OR wrap around in kernel time
				int up_time_us = up_time_ns / 1000;
				int down_time_us = down_time_ns / 1000;
				PR_ERR("DHT22: Negative diff_us: %d (high -> low [down]) - %d (low -> high [up]) = %d (diff_us)\n", down_time_us, up_time_us, diff_us);
				return -EINVAL; // TODO what error code?
			}
			this_byte = this_byte << 1; // shift current value to left to make room for new bit
			// shift before so last bit is not shifted too
			if (diff_ns > HIGH_THRESHOLD_NS)
			{
				// only have to set bit high if it is set, already zero'd entire array
				this_byte = this_byte | 1; // set high (current bit (last one))
			}
		}
		data[byte_index] = this_byte;
	}
	// todo compute value from data, do that later, lets see if this works
	PR_INFO("DHT22: humid: %d - %d   temp: %d - %d   checksum: %d\n", data[0], data[1], data[2], data[3], data[4]);

	// FYI gpio_desc ... now comes via device tree => platform device => iio device

	// FYI gpio_desc => https://github.com/raspberrypi/linux/blob/rpi-6.8.y/drivers/gpio/gpiolib.h#L157-L187

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

	// FYI protocol http://www.ocfreaks.com/basics-interfacing-dht11-dht22-humidity-temperature-sensor-mcu/
	// http://www.ocfreaks.com/imgs/embedded/dht/dhtxx_protocol.png
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

	dht22->irq = gpiod_to_irq(dht22->gpio_desc);
	if (dht22->irq < 0)
	{
		dev_err(dev, "GPIO %d has no interrupt\n", desc_to_gpio(dht22->gpio_desc));
		return -EINVAL;
	}

	// TODO, I don't think this is needed: // isn't devm_iio_device_alloc already setting this relationship... dont add unless I need it
	// platform_set_drvdata(pdev, iio);

	// init_completion(&dht22->completion); //
	// mutex_init(&dht22->lock); // TODO lock on read (one at a time)
	iio->name = pdev->name;
	iio->info = &dht22_iio_info;
	iio->modes = INDIO_DIRECT_MODE;
	iio->channels = dht22_chan_spec;
	iio->num_channels = ARRAY_SIZE(dht22_chan_spec);

	// platform_set_drvdata(pdev, iio); ! TODO do I need to switch request_irq mechanism, I don't think so yet... my null was on completion is my guess
	init_completion(&dht22->completion);

	return devm_iio_device_register(dev, iio); // link lifetime of iio device to platform device, thus when platform device is removed, iio device is removed (freeing resources of both)
}

static const struct of_device_id dht22_dt_ids[] = {
		{
				.compatible = "dht22iio-irq",
		},
		{}};
MODULE_DEVICE_TABLE(of, dht22_dt_ids);

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
