config DRM_PANIC
	bool "Display a user-friendly message when a kernel panic occurs"
	depends on DRM
	select FONT_SUPPORT
	help
	  Enable a drm panic handler, which will display a user-friendly message
	  when a kernel panic occurs. It's useful when using a user-space
	  console instead of fbcon.
	  It will only work if your graphic driver supports this feature.
	  To support Hi-DPI Display, you can enable bigger fonts like
	  FONT_TER16x32

config DRM_PANIC_FOREGROUND_COLOR
	hex "Drm panic screen foreground color, in RGB"
	depends on DRM_PANIC
	default 0xffffff

config DRM_PANIC_BACKGROUND_COLOR
	hex "Drm panic screen background color, in RGB"
	depends on DRM_PANIC
	default 0x000000

config DRM_PANIC_DEBUG
	bool "Add a debug fs entry to trigger drm_panic"
	depends on DRM_PANIC && DEBUG_FS
	help
	  Add dri/[device]/drm_panic_plane_x in the kernel debugfs, to force the
	  panic handler to write the panic message to this plane scanout buffer.
	  This is unsafe and should not be enabled on a production build.
	  If in doubt, say "N".

config DRM_PANIC_SCREEN
	string "Panic screen formatter"
	default "user"
	depends on DRM_PANIC
	help
	  This option enable to choose what will be displayed when a kernel
	  panic occurs. You can choose between "user", a short message telling
	  the user to reboot the system, or "kmsg" which will display the last
	  lines of kmsg.
	  This can also be overridden by drm.panic_screen=xxxx kernel parameter
	  or by writing to /sys/module/drm/parameters/panic_screen sysfs entry
	  Default is "user"

config DRM_PANIC_SCREEN_QR_CODE
	bool "Add a panic screen with a QR code"
	depends on DRM_PANIC && RUST
	help
	  This option adds a QR code generator, and a panic screen with a QR
	  code. The QR code will contain the last lines of kmsg and other debug
	  information. This should be easier for the user to report a kernel
	  panic, with all debug information available.
	  To use this panic screen, also set DRM_PANIC_SCREEN to "qr_code"

config DRM_PANIC_SCREEN_QR_CODE_URL
	string "Base URL of the QR code in the panic screen"
	depends on DRM_PANIC_SCREEN_QR_CODE
	help
	  This option sets the base URL to report the kernel panic. If it's set
	  the QR code will contain the URL and the kmsg compressed with zlib as
	  a URL parameter. If it's empty, the QR code will contain the kmsg as
	  uncompressed text only.
	  There is a demo code in javascript, to decode and uncompress the kmsg
	  data from the URL parameter at https://github.com/kdj0c/panic_report

config DRM_PANIC_SCREEN_QR_VERSION
	int "Maximum version (size) of the QR code."
	depends on DRM_PANIC_SCREEN_QR_CODE
	default 40
	help
	  This option limits the version (or size) of the QR code. QR code
	  version ranges from Version 1 (21x21) to Version 40 (177x177).
	  Smaller QR code are easier to read, but will contain less debugging
	  data. Default is 40.
