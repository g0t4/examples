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
