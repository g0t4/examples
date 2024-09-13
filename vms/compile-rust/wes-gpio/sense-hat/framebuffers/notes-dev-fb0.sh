
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

