time make -j$(nproc)

echo
echo

time sudo make modules_install

echo
echo

# remove old kernels b/c limited space on /boot partition and also I don't wanna see all of them in grub
sudo rm /boot/*6.11.0*
echo
echo
time sudo make install
