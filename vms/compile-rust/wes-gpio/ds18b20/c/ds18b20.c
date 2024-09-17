#define LOG_LEVEL_INFO 1
#define LOG_LEVEL_DEBUG 2
#define LOG_LEVEL LOG_LEVEL_DEBUG

#include <gpiod.h>
// sudo apt-get install libgpiod-dev
// dpkg -S gpiod.h => /usr/include/gpiod.h
#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include "logging.c"
#include <stdint.h>

#define LOW 0
#define HIGH 1
#define RELEASE HIGH

#define SKIP_ROM 0xCC
#define READ_ROM 0xBE
#define READ_SCRATCHPAD 0xBE

#define GPIO_CHIP_NAME "gpiochip4"
#define GPIO_CHIP_LABEL "pinctrl-rp1"
#define GPIO_LINE_DS18B20 12

void precise_delay_us(unsigned int us)
{
  struct timespec start, now;
  clock_gettime(CLOCK_MONOTONIC, &start);

  while (1)
  {
    clock_gettime(CLOCK_MONOTONIC, &now);
    long elapsed_us = (now.tv_sec - start.tv_sec) * 1e6 +
                      (now.tv_nsec - start.tv_nsec) / 1e3;
    if (elapsed_us >= us)
    {
      break;
    }
  }

  // FYI w1 therm driver in kernel impls spin timer => might be more accurate than what I am using above so consider it if more accurate timing is needed
  //  w1_delay https://github.com/raspberrypi/linux/blob/rpi-6.8.y/drivers/w1/w1_io.c#L40-L54
  //    unfortunately it uses udelay (kernel space only, IIUC => linux/asm/delay.h)
  //   https://github.com/raspberrypi/linux/blob/rpi-6.8.y/drivers/w1/w1_io.c#L342-L349
}

bool reset_bus(struct gpiod_line *line)
{
  // printf("line is %d\n", gpiod_line_get_value(line));
  gpiod_line_set_value(line, LOW);
  // printf("line is %d\n", gpiod_line_get_value(line));
  //  wait for 480us
  // usleep(480);
  precise_delay_us(480);
  // busy_wait(480);

  gpiod_line_set_value(line, HIGH);
  // printf("line is %d\n", gpiod_line_get_value(line));

  int start_us = clock();
  while (gpiod_line_get_value(line) == 1)
  {
    if (clock() - start_us > 1000000)
    {
      printf("timeout\n");
      break;
    }
    // printf("line is %d\n", gpiod_line_get_value(line));
  }
  // went low
  start_us = clock();
  while (gpiod_line_get_value(line) == 0)
  {
    if (clock() - start_us > 1000000)
    {
      printf("timeout\n");
      break;
    }
    // printf("line is %d\n", gpiod_line_get_value(line));
  }
  // released
  // need to wait >480us total before proceed
  int presence_us = clock() - start_us; // s/b 60 < presence_us < 120
  // printf("presence us: %d\n", presence_us);
  usleep(480 - presence_us); // must ensure entire presenece period is 480us

  return true;
}

bool send_command(struct gpiod_line *line, uint8_t command)
{
  // TODO analyze timing of 0=>0, 0=>1, 1=>0, 1=>1 (it looks like each has unique timing that can be perfected probably to avoid issues)
  bool prev_bit = 1; // s/b high and worse case we just wait a smidge longer on first writing first bit when its 1
  for (int i = 0; i < 8; i++)
  {
    // FYI bits are sent in reverse order
    bool this_bit = (command >> i) & 1;
    gpiod_line_set_value(line, HIGH); // ensure high // TODO do I need this?

    printf("bit: %d\n", this_bit);
    if (this_bit)
    {
      // write 1
      gpiod_line_set_value(line, LOW);
      // min 1us, max <15us
      if (prev_bit == 0)
      {
        precise_delay_us(2); // 0 => 1 needs less time to pull low again by not as high above threshold
      }
      else
      {
        precise_delay_us(5); // 1 => 1 needs more time to pull low b/c way above threshold
      }
      gpiod_line_set_value(line, HIGH);
      precise_delay_us(60); // 60 us total window (min)
    }
    else
    {
      // write 0
      gpiod_line_set_value(line, LOW);
      precise_delay_us(65); // min 60us => wow turned into 120us (LA1010),73us, 68us, 72us ...  120us breaks the rules (max 120)... the rest work inadvertently
      gpiod_line_set_value(line, HIGH);
      // PRN wait for it to be high? I am noticing that when I am low for along time and then go high, it seems to cut into recovery between bits
    }
    prev_bit = this_bit;
    precise_delay_us(3); // recovery >1us
  }

  printf("sent command: %d (%x)\n", command, command);
  // precise_delay_us(100);  //  TODO do I need this? I don't think so
  return true;
}

int main()
{

  if (CLOCKS_PER_SEC != 1000000)
  {
    printf("CLOCKS_PER_SEC is not 1_000_000 (us)\n");
    printf("CLOCKS_PER_SEC is %d\n", CLOCKS_PER_SEC);
    return 1;
  }

  // struct gpiod_chip *chip = gpiod_chip_open_by_name(GPIO_CHIP_NAME);
  struct gpiod_chip *chip = gpiod_chip_open_by_label(GPIO_CHIP_LABEL);
  if (!chip)
  {
    perror("Open GPIO chip failed");
    return 1;
  }

  struct gpiod_line *line = gpiod_chip_get_line(chip, GPIO_LINE_DS18B20);
  if (!line)
  {
    perror("Get GPIO line failed");
    gpiod_chip_close(chip);
    return 1;
  }

  // FYI also event based interface instead: gpiod_line_request_rising_edge_events, IIUC incompatible with read/write APIs
  int ret = gpiod_line_request_output(line, "my_program", HIGH); // keep high (unchanged initially)
  if (ret < 0)
  {
    perror("Request line as output failed");
    gpiod_chip_close(chip);
    return 1;
  }

  reset_bus(line) && send_command(line, SKIP_ROM);

  // cleanup
  gpiod_line_release(line);
  gpiod_chip_close(chip);

  return 0;
}
