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
#define READ_ROM 0x33
#define CONVERT_T_CMD 0x44
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

// return the bit that is read (negative if error) (0 is low, 1 is high)
int read_bit(struct gpiod_line *line)
{
  gpiod_line_set_value(line, HIGH); // might be vesitgial

  gpiod_line_set_value(line, LOW); // host starts the read by driving low for >1us but not long
  int start_time = clock();        // starts after pull low, have up to 15us to read the bit 0/1 for sure though I am seeing 31ish us for 0s, <5us for 1s

  // holy cow getting prev_bit (response_bits[-1]) had enough delay to mess up readings so don't use it here
  precise_delay_us(5); // since changing to 3, READ ROM has failed MUCH LESS OFTEN

  gpiod_line_set_value(line, HIGH);

  // simple idea => wait for the line to actually change before reading it (in the event it is a 1 and goes high rather quickly and we have a very very narrow window to read the line during b/c of stupid timing decisions)
  precise_delay_us(2); // give it time to actually change so hopefully don't need to re-read which can push past 15us window to read logic 1s

  while (gpiod_line_get_value(line) == LOW)
  { // ~3us to read
    if (clock() - start_time > 1e6)
    {
      printf("timeout - held low indefinitely - s/b NOT POSSIBLE\n");
      return -1;
    }
  }

  int us_low = clock() - start_time;

  // ensure 60us on 0 and 15us on 1
  int wait_more_us = 65 - us_low;
  // TODO try 15us on 1s
  if (wait_more_us > 0)
  {
    precise_delay_us(wait_more_us);
  }

  if (us_low > 15)
  {
    return LOW;
  }
  return HIGH;
}

/*  ! TODO either get diff impl of CRC8 or GPL release this code  */
static uint8_t w1_crc8_table[] = {
    0, 94, 188, 226, 97, 63, 221, 131, 194, 156, 126, 32, 163, 253, 31, 65,
    157, 195, 33, 127, 252, 162, 64, 30, 95, 1, 227, 189, 62, 96, 130, 220,
    35, 125, 159, 193, 66, 28, 254, 160, 225, 191, 93, 3, 128, 222, 60, 98,
    190, 224, 2, 92, 223, 129, 99, 61, 124, 34, 192, 158, 29, 67, 161, 255,
    70, 24, 250, 164, 39, 121, 155, 197, 132, 218, 56, 102, 229, 187, 89, 7,
    219, 133, 103, 57, 186, 228, 6, 88, 25, 71, 165, 251, 120, 38, 196, 154,
    101, 59, 217, 135, 4, 90, 184, 230, 167, 249, 27, 69, 198, 152, 122, 36,
    248, 166, 68, 26, 153, 199, 37, 123, 58, 100, 134, 216, 91, 5, 231, 185,
    140, 210, 48, 110, 237, 179, 81, 15, 78, 16, 242, 172, 47, 113, 147, 205,
    17, 79, 173, 243, 112, 46, 204, 146, 211, 141, 111, 49, 178, 236, 14, 80,
    175, 241, 19, 77, 206, 144, 114, 44, 109, 51, 209, 143, 12, 82, 176, 238,
    50, 108, 142, 208, 83, 13, 239, 177, 240, 174, 76, 18, 145, 207, 45, 115,
    202, 148, 118, 40, 171, 245, 23, 73, 8, 86, 180, 234, 105, 55, 213, 139,
    87, 9, 235, 181, 54, 104, 138, 212, 149, 203, 41, 119, 244, 170, 72, 22,
    233, 183, 85, 11, 136, 214, 52, 106, 43, 117, 151, 201, 74, 20, 246, 168,
    116, 42, 200, 150, 21, 75, 169, 247, 182, 232, 10, 84, 215, 137, 107, 53};

uint8_t w1_calc_crc8(uint8_t *data, int len)
{
  uint8_t crc = 0;

  while (len--)
    crc = w1_crc8_table[crc ^ *data++];

  return crc;
}

bool read_bytes(struct gpiod_line *line, uint8_t *bytes, size_t length)
{
  for (int i = 0; i < length; i++)
  {
    uint8_t byte = 0;
    for (int j = 0; j < 8; j++)
    {
      int bit = read_bit(line);
      if (bit < 0)
      {
        printf("Failed to read byte %d bit %d, aborting...\n", i, j);
        return false;
      }
      byte = byte | (bit << j);
    }
    bytes[i] = byte;
  }
  return true;
}

bool read_rom_response(struct gpiod_line *line)
{
  uint8_t all_bytes[8];
  if (!read_bytes(line, all_bytes, 8))
  {
    printf("Failed to read all bytes\n");
    return false;
  }

  printf("bytes:\n");
  for (int i = 0; i < 8; i++)
  {
    printf("  %08b (%d) hex: %02x\n", all_bytes[i], all_bytes[i], all_bytes[i]);
  }

  size_t length = sizeof(all_bytes) / sizeof(all_bytes[0]);
  uint8_t crc_all = w1_calc_crc8(all_bytes, length);
  if (crc_all != 0)
  {
    printf("Failed CRC check: %u\n", crc_all);
    return 0; // Or return an appropriate error code
  }
  printf("crc_all: %d\n", crc_all);

  uint8_t family_code = all_bytes[0]; // 8 bits (1 byte)
  uint8_t serial_number[6];           // 48 bits (6 bytes)
  for (int i = 0; i < 6; i++)
  {
    serial_number[5 - i] = all_bytes[i + 1];
  }
  uint8_t crc = all_bytes[7]; // 8 bits (1 byte)
  printf("Serial number: ");
  for (int i = 0; i < 6; i++)
  {
    printf("%02x", serial_number[i]);
  }
  printf("\n");
  printf("CRC: %d\n", crc);
  if (family_code != 0x28)
  {
    printf("Invalid family code: %02x, expected 0x28\n", family_code);
    return false;
  }

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

  printf("sent command: %d (%02x)\n", command, command);
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

  reset_bus(line) && send_command(line, READ_ROM);
  precise_delay_us(100); // TODO optimize (helped protocol analyzer identify fields)
  read_rom_response(line);

  // cleanup
  gpiod_line_release(line);
  gpiod_chip_close(chip);

  return 0;
}
