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
#define PR_INFO(fmt, ...) pr_info(fmt, ##__VA_ARGS__)
#define PR_ERR(fmt, ...) pr_err(fmt, ##__VA_ARGS__)
#else
#define PR_INFO(fmt, ...)
#define PR_ERR(fmt, ...)
#endif

#define GPIO_DATA_LINE RPI5_GPIO_4 // works well, FYI does not conflict with pins used by sense-hat

// IIO overview: https://wiki.analog.com/software/linux/docs/iio/iio
// use iio-tri-sysfs to trigger sample aquisition https://wiki.analog.com/software/linux/docs/iio/iio-trig-sysfs
//    use this to combine triggering and ring buffer (in software):
//      iio_triggered_buffer_setup_ext
//        takes iio_dev => makes iio_buffer

// kernel docs for GPIO => entrypoint explains legacy vs current (gpiod) APIs
// https://github.com/raspberrypi/linux/blob/rpi-6.8.y/Documentation/driver-api/gpio/intro.rst#L8
// legacy absolute GPIO numbering API => https://github.com/raspberrypi/linux/blob/rpi-6.8.y/Documentation/driver-api/gpio/legacy.rst#L1


static int read_raw(struct iio_dev *indio_dev,
                    struct iio_chan_spec const *chan,
                    int *val,
                    int *val2,
                    long mask)
{
  // read data from sensor
  // return data
  return 0;
}

static const struct iio_info dht22_iio_info = {
    .read_raw = read_raw,
};


static const struct iio_chan_spec dht22_chan_spec[] = {
	{ .type = IIO_TEMP,
		.info_mask_separate = BIT(IIO_CHAN_INFO_PROCESSED), },
	{ .type = IIO_HUMIDITYRELATIVE,
		.info_mask_separate = BIT(IIO_CHAN_INFO_PROCESSED), }
};

struct dht22 {
  struct iio_dev *indio_dev;
  struct device *dev;
  struct gpio_desc *gpio_desc;
  int irq;
};

static int dht22_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct dht22 *dht22;
	struct iio_dev *iio;

	iio = devm_iio_device_alloc(dev, sizeof(*dht22));
	if (!iio) {
		dev_err(dev, "Failed to allocate IIO device\n");
		return -ENOMEM;
	}

  dht22 = iio_priv(iio); // access (custom) private data
  dht22->dev = dev; // store platform device pointer
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
	{ .compatible = "dht22", },
	{ }
};
MODULE_DEVICE_TABLE(of, dht22_dt_ids);

#define DRIVER_NAME	"dht22"

static struct platform_driver dht22_driver = {
	.driver = {
		.name	= DRIVER_NAME,
		.of_match_table = dht22_dt_ids,
	},
	.probe  = dht22_probe,
};

module_platform_driver(dht22_driver); // instead of module_init and module_exit, for simple drivers
// __init/__exit via this macro =>  https://github.com/raspberrypi/linux/blob/rpi-6.8.y/include/linux/device/driver.h#L257-L268

MODULE_LICENSE("GPL"); // IF incompatible with other used modules, then compile fails! i.e. MIT here fails compile!
MODULE_AUTHOR("Wes Higbee");
MODULE_DESCRIPTION("dht22iio driver");
MODULE_VERSION("0.1");
