# pip install crcmod

import crcmod

# Define the CRC-8 function using the polynomial 0x131 (x^8 + x^5 + x^4 + 1)
ds18b20_crc8 = crcmod.mkCrcFun(0x131, initCrc=0, xorOut=0)

# readings that work out for CRC and have correct family code!!! yay getting closer to working!
# # Input bytes
#   00101000 (40)
#   01111100 (124)
#   10111100 (188)
#   00110010 (50)
#   00000000 (0)
#   00000000 (0)
#   00000000 (0)
#   11011010 (218)
# data = bytes([0x28, 0x7C, 0xBC, 0x32, 0x00, 0x00, 0x00])
data = bytes([40, 124, 188, 50, 0, 0, 0])  # => 218
# Calculate CRC
crc = ds18b20_crc8(data)
print(f"CRC-8: {crc}")

crc_all = ds18b20_crc8(data + bytes([crc]))
print(f"CRC-8 all: {crc_all} (should be 0)")


# SHOW SERIAL:
# Extract the 6-byte serial number (from byte 1 to byte 6, excluding family code and CRC)
serial_number_bytes = data[1:7]
print(f"Serial Number (Bytes): {serial_number_bytes}")

# Convert the 6-byte serial number to a hexadecimal string
serial_number_hex = ''.join(f'{byte:02X}' for byte in serial_number_bytes)

# Display the serial number
print(f"Serial Number (Hex): {serial_number_hex}")
