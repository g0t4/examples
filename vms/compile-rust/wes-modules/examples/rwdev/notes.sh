
ls /dev # before
sudo insmod rwdev.ko
ls /dev # after ! PROFIT
ls /dev/rwdev

sudo cat /dev/rwdev # hangs indefinitely currently
echo "foo" | sudo tee /dev/rwdev # works (NOOP currently)

sudo rmmod rwdev # unload works...
ls /dev/rwdev # gone! good

# ok its working:
sudo rmmod rwdev; sudo insmod rwdev.ko
sudo cat /dev/rwdev # shows initial message
echo "foo" | sudo tee /dev/rwdev
sudo cat /dev/rwdev # shows "foo"...
