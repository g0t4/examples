
ls /dev # before
sudo insmod dht22.ko
ls /dev # after ! PROFIT
ls /dev/dht22

sudo cat /dev/dht22 # hangs indefinitely currently
echo "foo" | sudo tee /dev/dht22 # works (NOOP currently)