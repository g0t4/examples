
# Found PANIC_SCREEN config option I forgot about...

# DOES NOT show qr code in my testing on the VM

# trying panic_screen sysfs entry (on VM):
echo -n "kmsg" > /sys/module/drm/parameters/panic_screen
# SHOWS KMSG on panic screen (i.e. blue)... instead of summarized panic screen
echo -n "user" > /sys/module/drm/parameters/panic_screen
# PUT IT BACK then disable/enable the debug mode to redraw panic screen user type:
echo 0 > /sys/kernel/debug/dri/simple-framebuffer.0/drm_panic_plane_0
echo 1 > /sys/kernel/debug/dri/simple-framebuffer.0/drm_panic_plane_0
# FOUND TOO:
cat /sys/module/drm/parameters/panic_qr_version


# menuconfig help:
# │ CONFIG_DRM_PANIC_SCREEN:                                                                                                                         │
# │                                                                                                                                                  │
# │ This option enable to choose what will be displayed when a kernel                                                                                │
# │ panic occurs. You can choose between "user", a short message telling                                                                             │
# │ the user to reboot the system, or "kmsg" which will display the last                                                                             │
# │ lines of kmsg.                                                                                                                                   │
# │ This can also be overridden by drm.panic_screen=xxxx kernel parameter                                                                            │
# │ or by writing to /sys/module/drm/parameters/panic_screen sysfs entry                                                                             │
# │ Default is "user"                                                                                                                                │
# │                                                                                                                                                  │
# │ Symbol: DRM_PANIC_SCREEN [=user]                                                                                                                 │
# │ Type  : string                                                                                                                                   │
# │ Defined at drivers/gpu/drm/Kconfig:139                                                                                                           │
# │   Prompt: Panic screen formatter                                                                                                                 │
# │   Depends on: HAS_IOMEM [=y] && DRM [=y] && DRM_PANIC [=y]                                                                                       │
# │   Location:                                                                                                                                      │
# │     -> Device Drivers                                                                                                                            │
# │       -> Graphics support                                                                                                                        │
# │         -> Direct Rendering Manager (XFree86 4.1.0 and higher DRI support) (DRM [=y])                                                            │
# │           -> Display a user-friendly message when a kernel panic occurs (DRM_PANIC [=y])                                                         │
# │             -> Panic screen formatter (DRM_PANIC_SCREEN [=user])
