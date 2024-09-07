
ls /dev # before
sudo insmod dht22.ko
ls /dev # after ! PROFIT
ls /dev/dht22

sudo cat /dev/dht22 # hangs indefinitely currently
echo "foo" | sudo tee /dev/dht22 # works (NOOP currently)

sudo rmmod dht22 # unload works...
ls /dev/dht22 # gone! good

# ok its working:
sudo rmmod dht22; sudo insmod dht22.ko
sudo cat /dev/dht22 # shows initial message
echo "foo" | sudo tee /dev/dht22
sudo cat /dev/dht22 # shows "foo"...
