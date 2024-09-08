# instructions: https://abyz.me.uk/rpi/pigpio/piscope.html

# deps
sudo apt install -y pigpio gtk+-3.0 # compile from src


wget abyz.me.uk/rpi/pigpio/piscope.tar
tar xvf piscope.tar
cd PISCOPE
make hf
make install

sudo pigpiod # not running the program... from docs it seems like maybe this library doesn't work with PI5? (only mentions up to 4B)?
# have to run terminal in xquartz else x11 forwarding won't work (i.e. from iterm2)


# test x11 forwarding
sudo apt install x11-apps
xeyes





# for hardware based logic analyzer (and other scopes):
# sudo apt install -y pulseview # frontend for sigrok https://sigrok.org/wiki/Main_Page
# sigrok h/w support: https://sigrok.org/wiki/Supported_hardware
