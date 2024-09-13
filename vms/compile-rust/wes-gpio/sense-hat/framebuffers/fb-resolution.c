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



  // get color map
  struct fb_cmap cmap;
  unsigned short *red, *green, *blue, *transp;
  int size = 128; // Assuming 256 colors (can vary)

  // Allocate memory for the color arrays
  red = (unsigned short *)malloc(sizeof(unsigned short) * size);
  green = (unsigned short *)malloc(sizeof(unsigned short) * size);
  blue = (unsigned short *)malloc(sizeof(unsigned short) * size);
  transp = (unsigned short *)malloc(sizeof(unsigned short) * size);

  if (!red || !green || !blue || !transp)
  {
    perror("Error allocating memory for colormap");
    close(fbfd);
    return -1;
  }

  cmap.start = 0;  // Start at color 0
  cmap.len = size; // Number of colors
  cmap.red = red;
  cmap.green = green;
  cmap.blue = blue;
  cmap.transp = transp;

  // Retrieve the color map with ioctl
  if (ioctl(fbfd, FBIOGETCMAP, &cmap) == -1)
  {
    perror("Error getting colormap");
    free(red);
    free(green);
    free(blue);
    free(transp);
    close(fbfd);
    return -1;
  }
  for (int i = 0; i < size; i++)
  {
    printf("Color %d: R=%u G=%u B=%u T=%u\n", i, cmap.red[i], cmap.green[i], cmap.blue[i], cmap.transp[i]);
  }
  free(red);
  free(green);
  free(blue);
  free(transp);

  close(fbfd);
  return 0;
}
