
# wait do I need to create the device node still... chatgpt said to do this:

# I want the driver to do this?
sudo mknod /dev/dht22 c <major_number> 0
# PRN use rwdev to redo /dev/dht22 to be full service within the driver?
