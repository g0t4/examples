
// IIO overview: https://wiki.analog.com/software/linux/docs/iio/iio
// use iio-tri-sysfs to trigger sample aquisition https://wiki.analog.com/software/linux/docs/iio/iio-trig-sysfs
//    use this to combine triggering and ring buffer (in software):
//      iio_triggered_buffer_setup_ext
//        takes iio_dev => makes iio_buffer

