# https://www.raspberrypi.com/products/sense-hat/
# https://pythonhosted.org/sense-hat/
from sense_hat import SenseHat

sense = SenseHat()

# i2c group required:
sense.get_humidity()
print(sense.temperature)

# input and video groups required:
sense.show_message("Hi, MOM!")

# sudo python3  demo.py
# must run as root (current permissions), or if not root:
#   in .venv => ModuleNotFoundError: No module named 'RTIMU'
#   in $HOME dir => Permission denied: '/dev/input/event5)
#     ls -l /dev/input/event5 # root:input (owner:group)... can I add myself to input group to not need sudo?
#     sudo usermod -aG input $USER
#   => next =>
#     Permission denied: '/dev/fb0'
#     sudo usermod -aG video $USER
#     PROFIT!!!!
#        ASIDE:    sudo dmesg | grep fb0  =>  fb0: RPi-Sense FB frame buffer device
#
