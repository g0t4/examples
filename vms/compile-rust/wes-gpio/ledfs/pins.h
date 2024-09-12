#ifndef RPI5_GPIO_H
#define RPI5_GPIO_H

// GLOBAL PIN NUMBERs for gpio_* functions (not for gpio_v2_* nor gpiod_* APIs)

#define RPI5_GPIO_BASE 571
// GPIO general purpose pins (not tied to protocol/driver like SPI, I2C, UART, PWM, EEPROM)
// LEFT SIDE
#define RPI5_GPIO_17 (RPI5_GPIO_BASE + 17) // left side, 6 down from top
#define RPI5_GPIO_27 (RPI5_GPIO_BASE + 27) // left side, 7 down
#define RPI5_GPIO_22 (RPI5_GPIO_BASE + 22) // left side, 8 down
#define RPI5_GPIO_4 (RPI5_GPIO_BASE + 4)   // left side, 4 down from top
#define RPI5_GPIO_5 (RPI5_GPIO_BASE + 5)   // left side, 6 up from bottom
#define RPI5_GPIO_6 (RPI5_GPIO_BASE + 6)   // left side, 5 up
#define RPI5_GPIO_26 (RPI5_GPIO_BASE + 26) // left side, 2 up
// RIGHT SIDE
#define RPI5_GPIO_23 (RPI5_GPIO_BASE + 23) // right side, 8 down from top
#define RPI5_GPIO_24 (RPI5_GPIO_BASE + 24) // right side, 9 down
#define RPI5_GPIO_25 (RPI5_GPIO_BASE + 25) // right side, 11 down
#define RPI5_GPIO_16 (RPI5_GPIO_BASE + 16) // right side, 3 up from bottom
// end GPIO general purpose pins

#endif // RPI5_GPIO_H
