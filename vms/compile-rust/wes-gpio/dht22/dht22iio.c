#include <linux/iio/iio.h>

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

static const struct iio_info dht11_iio_info = {
    .read_raw = read_raw,
};

MODULE_LICENSE("GPL");
