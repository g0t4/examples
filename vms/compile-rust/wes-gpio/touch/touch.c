// TODO clean up unused imports
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
#include <linux/input.h> // for input subsystem (keyboards, mouse, buttons, etc)
#include "../ledfs/pins.h"

struct touch_sensor_struct
{
  struct gpio_desc *gpio_desc;
  int irq;
  struct input_dev *input_dev;
};

static irqreturn_t touch_irq_handler(int irq, void *dev_id)
{
  struct touch_sensor_struct *touch_sensor = dev_id;
  // IRQ handler for touch sensor's GPIO pin (edge triggered IRQs)... so now we generate input events (for keyboard or otherwise)

  int value = gpiod_get_value(touch_sensor->gpio_desc); // get current high/low
  if (value == 0)
  {
    // just pressed
    input_report_key(touch_sensor->input_dev, KEY_ENTER, 1); // ENTER?! do I really want that?
    input_sync(touch_sensor->input_dev);
  }
  else
  {
    // just depressed
    input_report_key(touch_sensor->input_dev, KEY_ENTER, 0);
    input_sync(touch_sensor->input_dev);
  }
  return IRQ_HANDLED;
}

static int touch_sensor_probe(struct platform_device *pdev)
{
  struct device *dev = &pdev->dev;
  struct touch_sensor_struct *touch_sensor;
  struct input_dev *inputdev;

  inputdev = devm_input_allocate_device(dev); // todo chatgpt didn't use devm, used input_allocate_device() alone (no ref to pdev/dev... that can't work? how would it link devices?)
  if (!inputdev)
  {
    dev_err(dev, "Failed to allocate input device\n");
    return -ENOMEM;
  }

  touch_sensor = devm_kzalloc(dev, sizeof(struct touch_sensor_struct), GFP_KERNEL);

  // PRN do I want this: (only if helps for error handling)
  // if (!gpio_is_valid(GPIO_PIN_NUMBER)) {
  //     dev_err(&pdev->dev, "Invalid GPIO\n");
  //     return -ENODEV;
  // }

  touch_sensor->gpio_desc = devm_gpiod_get(dev, NULL, GPIOD_IN); // input mode
  //  get desc should fail if its an invalid pin, right? would it be useful to check if valid though for error messages purpose?
  if (IS_ERR(touch_sensor->gpio_desc))
    return PTR_ERR(touch_sensor->gpio_desc);

  inputdev->name = pdev->name;                                 // todo do I want smth else? did this from dht22iio driver
  inputdev->evbit[0] = BIT_MASK(EV_KEY);                       // todo what is this, chatgpt suggested
  inputdev->keybit[BIT_WORD(KEY_ENTER)] = BIT_MASK(KEY_ENTER); // TODO what is this chatgpt

  int ret = input_register_device(inputdev);
  if (ret != 0) // TODO what is expected return on this? != 0 right == error, right? chatgpt suggested if(ret).. yuck.. .as if ret was an error
  {
    input_free_device(inputdev);
    return ret;
  }

  // IRQ handler
  touch_sensor->irq = gpiod_to_irq(touch_sensor->gpio_desc);
  touch_sensor->input_dev = inputdev;
  ret = request_irq(touch_sensor->irq, touch_irq_handler, IRQF_TRIGGER_FALLING | IRQF_TRIGGER_RISING, "touch_sensor_irq", touch_sensor);
  if (ret != 0)
  {
    input_unregister_device(inputdev);
    return ret;
  }

  dev_info(&pdev->dev, "touch_sensor driver initialized\n");

  platform_set_drvdata(pdev, touch_sensor);
  return 0;
}

static int touch_sensor_remove(struct platform_device *pdev)
{
  struct touch_sensor_struct *touch_sensor = platform_get_drvdata(pdev);

  free_irq(touch_sensor->irq, NULL);
  input_unregister_device(touch_sensor->input_dev);
  return 0;
}

#define DRIVER_NAME "touch_sensor"
static struct platform_driver touch_sensor_driver = {
    .probe = touch_sensor_probe,
    .remove = touch_sensor_remove,
    .driver = {
        .name = DRIVER_NAME,
        .owner = THIS_MODULE,
    },
};

module_platform_driver(touch_sensor_driver); // wires up to init/exit functions

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Capacitive Touch Driver");
MODULE_AUTHOR("Wes Higbee");