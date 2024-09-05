time make -j$(nproc)

echo
echo 

time sudo make modules_install

echo
echo 

sudo rm /boot/*6.11.0*
echo
echo 
time sudo make install
