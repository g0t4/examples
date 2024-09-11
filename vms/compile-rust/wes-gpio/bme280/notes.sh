
# FYI I found this in iio bindings:

# BME280 device tree bindings:
#   docs: Documentation/devicetree/bindings/iio/pressure/bmp085.yaml
#     title: BMP085/BMP180/BMP280/BME280/BMP380 pressure iio sensors
#     description: Pressure, temperature and humidity iio sensors with i2c and spi interfaces
#     FYI https://www.adafruit.com/product/391 (bmp085)
#
#    IIUC impl'd in driver: drivers/iio/pressure/bmp280-i2c.c
#            or bmp280-spi.c

# depmod generates modules.alias file to map devices to drivers (in kernel drivers)
cat /lib/modules/$(uname -r)/modules.alias | grep -i bme280

