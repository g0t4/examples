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

  bool pressed; // TODO do I need/want this, to read its current depressed state? like holding a key down vs released?
};

static struct touch_sensor_struct touch_sensor;
// todo can I link my static structs to platform_device somehow? and use that arg in various methods?
static struct input_dev *inputdev;

static irqreturn_t touch_irq_handler(int irq, void *dev_id)
{
  // IRQ handler for touch sensor's GPIO pin (edge triggered IRQs)... so now we generate input events (for keyboard or otherwise)

  int value = gpiod_get_value(touch_sensor.gpio_desc); // get current high/low
  if (value == 0)
  {
    // just pressed
    input_report_key(inputdev, KEY_ENTER, 1); // ENTER?! do I really want that?
    input_sync(inputdev);
  }
  else
  {
    // just depressed
    input_report_key(inputdev, KEY_ENTER, 0);
    input_sync(inputdev);
  }
  return IRQ_HANDLED;
}

static int ttp223_probe(struct platform_device *pdev)
{
  struct device *dev = &pdev->dev;

  inputdev = devm_input_allocate_device(dev); // todo chatgpt didn't use devm, used input_allocate_device() alone (no ref to pdev/dev... that can't work? how would it link devices?)
  if (!inputdev)
  {
    dev_err(dev, "Failed to allocate input device\n");
    return -ENOMEM;
  }

  // PRN do I want this: (only if helps for error handling)
  // if (!gpio_is_valid(TTP223_GPIO_PIN)) {
  //     dev_err(&pdev->dev, "Invalid GPIO\n");
  //     return -ENODEV;
  // }

  touch_sensor.gpio_desc = devm_gpiod_get(dev, NULL, GPIOD_IN); // input mode
  //  get desc should fail if its an invalid pin, right? would it be useful to check if valid though for error messages purpose?
  if (IS_ERR(touch_sensor.gpio_desc))
    return PTR_ERR(touch_sensor.gpio_desc);

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
  touch_sensor.irq = gpiod_to_irq(touch_sensor.gpio_desc);
  ret = request_irq(touch_sensor.irq, touch_irq_handler, IRQF_TRIGGER_FALLING | IRQF_TRIGGER_RISING, "touch_sensor_irq", NULL);
  if (ret != 0)
  {
    input_unregister_device(inputdev);
    return ret;
  }

  dev_info(&pdev->dev, "TTP223 driver initialized\n");
  return 0;
}

static int ttp223_remove(struct platform_device *pdev)
{
  int irq_number = 0; // TODO pdev=>touch_sensor

  free_irq(irq_number, NULL);
  input_unregister_device(inputdev);
  // gpio_free(TTP223_GPIO_PIN); // do I care to do this? can't I just use it w/o requesting/locking it?
  return 0;
}

static struct platform_driver ttp223_driver = {
    .probe = ttp223_probe,
    .remove = ttp223_remove,
    .driver = {
        .name = "ttp223",
        .owner = THIS_MODULE,
    },
};

module_platform_driver(ttp223_driver); // wires up to init/exit functions

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Capacitive Touch Driver");
MODULE_AUTHOR("Wes Higbee");