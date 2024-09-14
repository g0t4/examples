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
  int gpio_pin;
  int irq;
  struct input_dev *input_dev;
};

static char *get_pin_info(struct touch_sensor_struct *touch_sensor)
{
  int main_gpio_pin = touch_sensor->gpio_pin - RPI5_GPIO_BASE;
  char *msg = kzalloc(200, GFP_KERNEL);
  snprintf(msg, 200, "GPIO pin %d (irq %d)", main_gpio_pin, touch_sensor->irq);
  return msg;
}

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

  touch_sensor->gpio_desc = devm_gpiod_get(dev, NULL, GPIOD_IN);
  if (IS_ERR(touch_sensor->gpio_desc))
  {
    dev_err(dev, "Failed to get GPIO descriptor for %s\n", get_pin_info(touch_sensor));
    input_free_device(inputdev);
    kfree(touch_sensor);
    return PTR_ERR(touch_sensor->gpio_desc);
  }

  touch_sensor->gpio_pin = desc_to_gpio(touch_sensor->gpio_desc);
  dev_info(dev, "probing %s\n", get_pin_info(touch_sensor));

  inputdev->name = pdev->name;                                 // todo do I want smth else? did this from dht22iio driver
  inputdev->evbit[0] = BIT_MASK(EV_KEY);                       // todo what is this, chatgpt suggested
  inputdev->keybit[BIT_WORD(KEY_ENTER)] = BIT_MASK(KEY_ENTER); // TODO what is this chatgpt

  int ret = input_register_device(inputdev);
  if (ret)
  {
    dev_err(dev, "Failed to register input device (ret=%d) for %s\n", ret, get_pin_info(touch_sensor));
    input_free_device(inputdev);
    kfree(touch_sensor);
    return ret;
  }

  // ! TODO switch to devm_request_irq (should auto free up irq on driver unload), right before that need to get irq_num:
  // int irq_num = platform_get_irq(pdev, 0);  // Get IRQ from platform device
  // if (irq_num < 0) {
  //     dev_err(&pdev->dev, "Failed to get IRQ\n");
  //     return irq_num;
  // }
  // ! INSTEAD OF gpiod_to_irq + request_irq.. oh is it possible I am using wrong irq from GPIO and not for my device itself?!
  // IRQ handler
  touch_sensor->irq = gpiod_to_irq(touch_sensor->gpio_desc);
  touch_sensor->input_dev = inputdev;
  ret = request_irq(touch_sensor->irq, touch_irq_handler, IRQF_TRIGGER_FALLING | IRQF_TRIGGER_RISING, "touch_sensor_irq", touch_sensor);
  if (ret) // success => ret == 0 (odd part of request_irq)
  {
    dev_err(dev, "request_irq FAILED (ret=%d) for %s\n", ret, get_pin_info(touch_sensor));
    input_unregister_device(inputdev);
    kfree(touch_sensor);
    return ret;
  }

  dev_info(dev, "probed %s\n", get_pin_info(touch_sensor));

  platform_set_drvdata(pdev, touch_sensor);

  return 0;
}

static int touch_sensor_remove(struct platform_device *pdev)
{
  struct touch_sensor_struct *touch_sensor = platform_get_drvdata(pdev);
  dev_info(&pdev->dev, "removing %s\n", get_pin_info(touch_sensor));

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