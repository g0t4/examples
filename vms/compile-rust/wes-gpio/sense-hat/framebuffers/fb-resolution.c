#include <stdio.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/fb.h>
#include <unistd.h>
#include <stdlib.h>

int main()
{
  int fbfd = open("/dev/fb0", O_RDWR);
  if (fbfd == -1)
  {
    perror("Error opening framebuffer device");
    return -1;
  }

  struct fb_var_screeninfo vinfo;
  // use ioctl to query framebuffer devices, per https://www.kernel.org/doc/Documentation/fb/framebuffer.txt
  //    se linux/fb.h for the struct definitions
  if (ioctl(fbfd, FBIOGET_VSCREENINFO, &vinfo))
  {
    perror("Error reading variable information");
    return -1;
  }

  printf("Resolution: %dx%d\n", vinfo.xres, vinfo.yres);
  printf("Bits per pixel: %d\n", vinfo.bits_per_pixel);
  // senese-hat: 8x8

  struct fb_fix_screeninfo finfo;
  if (ioctl(fbfd, FBIOGET_FSCREENINFO, &finfo))
  {
    perror("Error reading fixed information");
    return -1;
  }
  printf("\nFixed info:\n");
  printf("  smem_len: %d\n", finfo.smem_len);
  printf("  line_length: %d\n", finfo.line_length);
  int size = 1 << vinfo.bits_per_pixel;
  printf("Number of colors (size of color map): %d\n", size);

  close(fbfd);
  return 0;
}
