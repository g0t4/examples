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
#define ASSUME_PREV_HIGH HIGH

// ROM commands
#define SKIP_ROM 0xCC
#define READ_ROM 0x33
#define SEARCH_ROM 0xF0
#define MATCH_ROM 0x55
#define ALARM_SEARCH 0xEC

// memory commands (must come after a ROM command)
#define CONVERT_T_CMD 0x44
#define READ_SCRATCHPAD 0xBE
#define RECALL_E2 0xB8
#define WRITE_SCRATCHPAD 0x4E
#define COPY_SCRATCHPAD 0x48
#define MEMORY_READ_POWER_SUPPLY 0xB4 // PRN rename other memory commands that aren't obvious, maybe prefix all with MEMORY_ (that way I can easily spot if I am using commands in the wrong order)

#define GPIO_CHIP_NAME "gpiochip4"
#define GPIO_CHIP_LABEL "pinctrl-rp1"
#define GPIO_LINE_DS18B20 12

bool precise_delay_us(unsigned int us)
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
  return true; // just so I can compose with other boolean operations
  // FYI w1 therm driver in kernel impls spin timer => might be more accurate than what I am using above so consider it if more accurate timing is needed
  //  w1_delay https://github.com/raspberrypi/linux/blob/rpi-6.8.y/drivers/w1/w1_io.c#L40-L54
  //    unfortunately it uses udelay (kernel space only, IIUC => linux/asm/delay.h)
  //   https://github.com/raspberrypi/linux/blob/rpi-6.8.y/drivers/w1/w1_io.c#L342-L349
}

bool reset_bus(struct gpiod_line *line)
{
  gpiod_line_set_value(line, LOW);

  precise_delay_us(480);

  gpiod_line_set_value(line, HIGH);

  int start_us = clock();
  while (gpiod_line_get_value(line) == 1)
  {
    if (clock() - start_us > 1000000)
    {
      LOG_ERROR("timeout waiting for line to go low - the start of presence response");
      break;
    }
  }
  // just went low
  start_us = clock();

  while (gpiod_line_get_value(line) == 0)
  {
    if (clock() - start_us > 1000000)
    {
      LOG_ERROR("timeout waiting for line to go high - the end of presence response");
      break;
    }
  }
  // released

  // must wait 480us past start of presence response
  int presence_us = clock() - start_us; // s/b 60 < presence_us < 120
  usleep(480 - presence_us);

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
      LOG_ERROR("timeout - held low indefinitely - s/b NOT POSSIBLE");
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

bool read_bytes(struct gpiod_line *line, uint8_t *bytes, size_t num_bytes)
{
  for (int byteIndex = 0; byteIndex < num_bytes; byteIndex++)
  {
    uint8_t current_byte = 0;
    for (int bitIndex = 0; bitIndex < 8; bitIndex++)
    {
      int bit = read_bit(line);
      if (bit < 0)
      {
        LOG_ERROR("Failed to read byte %d bit %d, aborting...", byteIndex, bitIndex);
        return false;
      }
      // reads: put bit into current_byte at position bitIndex
      // thus we assemble the byte from left to right (reverse of how we read it)
      current_byte = (bit << bitIndex) | current_byte;
    }
    bytes[byteIndex] = current_byte;
  }

  LOG_DEBUG("%d bytes read:", num_bytes);
  for (int i = 0; i < 8; i++)
  {
    // FYI %08b is not standard C, but it is in glibc? IIUC
    LOG_DEBUG("  %08b (0x%02x = %3d)", bytes[i], bytes[i], bytes[i]);
  }

  return true;
}

bool read_bytes_with_crc(struct gpiod_line *line, uint8_t *bytes, size_t num_bytes)
{
  if (!read_bytes(line, bytes, num_bytes))
  {
    return false;
  }

  // FYI crc(bytes) == 0
  //   OR crc(bytes[0:7]) == bytes[8]
  uint8_t crc = w1_calc_crc8(bytes, num_bytes);
  if (crc != 0)
  {
    LOG_ERROR("Failed CRC check: %u", crc);
    return 0; // Or return an appropriate error code
  }
  return true;
}

bool read_rom_response(struct gpiod_line *line)
{
  uint8_t all_bytes[8];
  if (!read_bytes_with_crc(line, all_bytes, 8))
  {
    return false;
  }

  uint8_t family_code = all_bytes[0]; // 8 bits (1 byte)
  uint8_t serial_number[6];           // 48 bits (6 bytes)
  for (int i = 0; i < 6; i++)
  {
    serial_number[5 - i] = all_bytes[i + 1];
  }

  char serial_number_string[13];
  sprintf(serial_number_string, "%02x%02x%02x%02x%02x%02x", serial_number[0], serial_number[1], serial_number[2], serial_number[3], serial_number[4], serial_number[5]);
  LOG_DEBUG("serial number: %s", serial_number_string);

  if (family_code != 0x28)
  {
    LOG_ERROR("Invalid family code %02x, expected 0x28", family_code);
    return false;
  }

  return true;
}

bool read_scratchpad(struct gpiod_line *line)
{
  uint8_t scratchpad[9];
  if (!read_bytes_with_crc(line, scratchpad, 9))
  {
    return false;
  }

  uint8_t temp_lsb = scratchpad[0];
  uint8_t temp_msb = scratchpad[1];
  int16_t temp_raw = (temp_msb << 8) | temp_lsb;
  if (temp_raw & 0x8000)
  {
    temp_raw = -((temp_raw ^ 0xFFFF) + 1);
  }
  float temp_celsius = temp_raw / 16.0;
  LOG_INFO("Temp: %.2f°C", temp_celsius);
  float temp_fahrenheit = temp_celsius * 9 / 5 + 32;
  LOG_INFO("Temp: %.2f°F", temp_fahrenheit);

  // PRN read rest of scratchpad beyond temperature when I need it and build a struct response?

  return true;
}

bool write_bit(struct gpiod_line *line, bool this_bit, bool prev_bit)
{
  gpiod_line_set_value(line, HIGH); // ensure high // TODO do I need this?

  LOG_DEBUG("writing bit: %d", this_bit);
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
  precise_delay_us(3); // recovery >1us
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
    if (!write_bit(line, this_bit, prev_bit))
    {
      return false; // assume inner write_bit already logged explanation
    }
    prev_bit = this_bit;
  }

  switch (command)
  {

    // ROM commands
  case SKIP_ROM:
    LOG_INFO("sent command: SKIP_ROM 0x%02x", SKIP_ROM);
    break;
  case READ_ROM:
    LOG_INFO("sent command: READ_ROM 0x%02x", READ_ROM);
    break;
  case SEARCH_ROM:
    LOG_INFO("sent command: SEARCH_ROM 0x%02x", SEARCH_ROM);
    break;
  case MATCH_ROM:
    LOG_INFO("sent command: MATCH_ROM 0x%02x", MATCH_ROM);
    break;

    // Memory commands
  case CONVERT_T_CMD:
    LOG_INFO("sent command: CONVERT_T_CMD 0x%02x", CONVERT_T_CMD);
    break;
  case READ_SCRATCHPAD:
    LOG_INFO("sent command: READ_SCRATCHPAD 0x%02x", READ_SCRATCHPAD);
    break;
  case WRITE_SCRATCHPAD:
    LOG_INFO("sent command: WRITE_SCRATCHPAD 0x%02x", WRITE_SCRATCHPAD);
    break;
  case COPY_SCRATCHPAD:
    LOG_INFO("sent command: COPY_SCRATCHPAD 0x%02x", COPY_SCRATCHPAD);
    break;
  case RECALL_E2:
    LOG_INFO("sent command: RECALL_E2 0x%02x", RECALL_E2);
    break;
  case MEMORY_READ_POWER_SUPPLY:
    LOG_INFO("sent command: READ_POWER_SUPPLY 0x%02x", MEMORY_READ_POWER_SUPPLY);
    break;
  default:
    LOG_INFO("sent generic command: %d (0x%02x) - please add command name to list to show meaningful name", command, command);
    break;
  }

  return true;
}

bool wait_for_temp_conversion_to_complete(struct gpiod_line *line)
{
  // FYI if parasite power, need to hold data line HIGH for 750ms (Tconv)
  //   IIAC trying a read slot during parasite power would interrupt and corrupt the Convert T command
  //   if external power, can use read slots to check status
  //   probably best just to always wait 750ms b/c what is 100ms less gonna matter?!
  //

  // FYI if you call Convert T then it writes to memory a temp value and subsequent reads will work without this delay... so the first time you boot up and request temp you need to manually ywait to get around hte 750ms min on 12-bit resolution
  // TODO fix this, why isn't it working? also look at python impl and fix it too if fixed here
  // ! TODO check manual - says smth about 10us to release bus after convert T command... am I doing that? why does this successfully wait for read slot to return 1 after 600ms and then read scratch pad always fails?
  // FYI this issue is not waiting, but READ_SCRATCHPAD always fails

  // WTF, now, waiting for a second results in read scratch pad CRC failures... WTF? without delay I am reading an old value, reliably?!
  // precise_delay_us(1000000);
  return true;
  int start_time = clock();
  while (1)
  {
    int bit = read_bit(line);
    if (bit < 0)
    {
      int elapsed_ms = (clock() - start_time) / 1000;
      LOG_ERROR("Failed to read bit for status of temp conversion, aborting after %d ms", (clock() - start_time) / 1000);
      return false;
    }
    if (bit == 1)
    {
      int elapsed_ms = (clock() - start_time) / 1000;
      LOG_INFO("Temp conversion complete after %d ms", elapsed_ms);
      break;
    }
    if (clock() - start_time > 1e6)
    {
      LOG_ERROR("Timeout waiting for temp conversion to complete");
      return false;
    }
    precise_delay_us(50000); // check every 50ms
  }

  return true;
}

bool search_rom(struct gpiod_line *line)
{
  send_command(line, SEARCH_ROM);

  uint8_t read1 = read_bit(line);
  uint8_t read2 = read_bit(line);
  // | read1 | read2 |
  // |   0   |   0   |   sensor(s) remaining with 0 and 1
  // |   0   |   1   |   sensor(s) remaining with 0, none with 1
  // |   1   |   0   |   sensor(s) remaining with 1, none with 0
  // |   1   |   1   |   no sensors (remaining)

  // create an array of  to store discovered bits and help sequence the search
  return false; // TODO
}

bool read_power_supply_type(struct gpiod_line *line)
{
  bool success = reset_bus(line)                 //
                 && send_command(line, SKIP_ROM) //
                 && send_command(line, MEMORY_READ_POWER_SUPPLY);
  if (!success)
  {
    LOG_ERROR("Failed to send command to read power supply type");
    return false;
  }
  int response = read_bit(line);
  if (response < 0)
  {
    LOG_ERROR("Failed to read power supply status bit");
    return false;
  }
  // PRN extract method that can return power supply type for code branching (i.e. to know to wait 750ms versus reading status bit on Convert T)
  if (response)
  {
    LOG_INFO("External power supply: %d", response);
    return true;
  }
  LOG_INFO("Parasite power (using data line, no external power): %d", response);
  return true;
}

int main()
{

  if (CLOCKS_PER_SEC != 1000000)
  {
    LOG_ERROR("CLOCKS_PER_SEC is not 1_000_000 (us), it is %d", CLOCKS_PER_SEC);
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

  // TODO remove or optimize the precise_delay_us(100) - added to help protocol analyzer identify fields clearly

  // reset_bus(line) && send_command(line, READ_ROM) //
  //     && precise_delay_us(100) && read_rom_response(line);

  // reset_bus(line) && send_command(line, SKIP_ROM)                                 // use comment to stop vcformat from combining lines (hack for now)
  //     && precise_delay_us(100) && send_command(line, CONVERT_T_CMD)               //
  //     && wait_for_temp_conversion_to_complete(line)                               //
  //     && precise_delay_us(100) && reset_bus(line) && send_command(line, SKIP_ROM) //
  //     && precise_delay_us(100) && send_command(line, READ_SCRATCHPAD) && read_scratchpad(line);

  // reset_bus(line) && search_rom(line); // for multi device setups =

  read_power_supply_type(line);

  // cleanup
  gpiod_line_release(line);
  gpiod_chip_close(chip);

  return 0;
}
