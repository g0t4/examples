
# directly using /dev/fb0


# hex => binary => /dev/fb0
echo "000000000000" | xxd -r -p | sudo tee /dev/fb0
# -r = reverse => convert hex to binary
# -p = plain => no spaces, line breaks, address

# current fb content (dump in hex):
cat /dev/fb0 | xxd
cat /dev/fb0 | hexdump -C

# find len of fb0
set fb0len (cat /dev/fb0 | xxd -p | wc -c) # => 261 chars

yes 0 | head -n 130 | tr -d '\n' | xxd -r -p | sudo tee /dev/fb0
yes 1 | head -n 257 | tr -d '\n' | xxd -r -p | sudo tee /dev/fb0 # works
yes 1 | head -n 261 | tr -d '\n' | xxd -r -p | sudo tee /dev/fb0 # too many subseequent times... todo why?

# don't forget:
fbset -s
# mode "8x8"
#     geometry 8 8 8 8 16
#     timings 0 0 0 0 0 0 0
#     rgba 5/11,6/5,5/0,0/0
# endmode

# 8x8 grid, color depth 4 hex digits => 65K color? (16 bits)
# https://www.raspberrypi.com/documentation/accessories/sense-hat.html

# fb docs: https://www.kernel.org/doc/Documentation/fb/framebuffer.txt
#  /dev/fb*
#  char device with major number 29
# snapshot with:
cp /dev/fb0 myfile
export FRAMEBUFFER=/dev/fb1 # pick with framebuffer for an app
# memory like device, like /dev/mem # read/write/seek/mmap
# ioctl() system call provides details, i.e. color map IIUC

# use bits to hex to make sure I know which bits are on/off easily (no translation to/from hex)
echo "10000 0 0 0" | ./bits_to_hex.py | xxd -r -p | sudo tee /dev/fb0
cat /dev/fb0
#
# fbset -s =>  rgba 5/11,6/5,5/0,0/0
#   RRRRR_GGG GGG_BBBBB
# 16 bit word size (2 bytes)
# from my tinkering, it seems each pixel's bit layout for colors is:
# GGG_BBBBB RRRRR_GGG # little endian layout: LSB MSB (for 2 byte, or 16 bit word)
lscpu | grep "Byte Order" # => Little Endian
# so that maps to:
# RRRRR_GGG GGG_BBBBB # big endian layout (easier to reason about bit positions IMO)
# https://en.wikipedia.org/wiki/Endianness
#
# don't conflate the order of pixels in memory with the order of bytes in each pixel's value...
# that said... pixel layout starts with lower right, moves left across bottom row, then up a row and to right side... all the way to upper left (row by row)

# BTW I now strip underscores so you can use them to split up color positions... just don't forget each subset left/right of _ is not separate value... you need 8 bits in a row regardless:
echo "000_00000 00000_100" | ./bits_to_hex.py | xxd -r -p | sudo tee /dev/fb0
# think "GGG_BBBBB RRRRR_GGG"  make sure to include all 8 bits for each byte else it won't be the value you expect, I made that mistake a few times when testing color bit masks... and threw me off!

