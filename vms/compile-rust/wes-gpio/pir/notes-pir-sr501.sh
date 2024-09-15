

# using touch driver (IIUC motion via infrared sensor triggers line to go high)
sudo dtoverlay touch-sensor-unified.dtbo gpio_pin=12

# listen to key presses from touch driver
evtest /dev/input/by-path/platform-touch_sensor_unified@c-event

# FYI did not work when I used GPIO=23 (not sure why, failed to probe the GPIO, can't recall reason in dmesg)