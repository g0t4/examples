#!/usr/bin/env python3
import sys

s = sys.stdin.read().strip().replace('_','') # allow _ to split bytes into 4 bits or less
bytes = s.split(' ') # space delimited bytes
# print(bytes([int(s[i:i + 8], 2) for i in range(0, len(s), 8)]).hex())
for bit_group in bytes:
    byte_value = int(bit_group, 2)
    print(f"{byte_value:02x}", end='')

# USAGE:
# echo "0101 00110111" | ./bits_to_hex.py # => 0537  # zero padded if < 8 bits per byte
# echo "0101 00110111" | ./bits_to_hex.py | xxd -r -p | xxd # confirm xxd to binary works by reversing it
# echo "0101 00110111" | ./bits_to_hex.py | xxd -r -p | sudo tee /dev/fb1 # write to framebuffer
# echo "00000101 00110111" | ./bits_to_hex.py # => 0537


# later on:
# echo "00000000 00000010" | ./bits_to_hex.py | xxd -r -p | sudo tee /dev/fb0 # green
# echo "0 00000010 0 0" | ./bits_to_hex.py | xxd -r -p | sudo tee /dev/fb0  # turn off with just 0

# see notes for more