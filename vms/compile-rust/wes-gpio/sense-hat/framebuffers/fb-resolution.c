#include <stdio.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/fb.h>
#include <unistd.h>

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

  struct fb_cmap cmap;
  if (ioctl(fbfd, FBIOGETCMAP, &cmap))
  {
    perror("Error reading cmap information");
    return -1;
  }
  printf("\ncmap:\n");
  printf("  start: %d\n", cmap.start);
  printf("  len: %d\n", cmap.len);
  for (int i = 0; i < cmap.len; i++)
  {
    printf("  red: %d, green: %d, blue: %d, transp: %d\n", cmap.red[i], cmap.green[i], cmap.blue[i], cmap.transp[i]);
  }

  close(fbfd);
  return 0;
}
