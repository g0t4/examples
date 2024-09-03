btw use:
grep DRM_PANIC /boot/config-*  # check actual last installed vs src dir (might have partial/wip install not yet actuall sys installed)


Use 6.8 on any of these for no panic screen at all (show why that is a problem)

# macos qemu VM (neither currently qr code capable)
- black => rc5-next
- blue => 6.11.0-qrcodewes-next-20240830

# guestVM on build13
- only qr code build (with qr code flags enabled minus qr_code into drm module parameters)






# build13 (neither currently qr code capable)
STOP USING this machine's custom kernel builds (confusing to me)...  naming of dirs vs extraversion IS UGH
  somehow it seems the config for qr codes is just Fing missing too on both kernels built...  did a menu makeconmfig or recommpile turn off options for QR code?!
