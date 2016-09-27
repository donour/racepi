#define _GNU_SOURCE
#define DEV_INPUT_EVENT "/dev/input"
#define EVENT_DEV_NAME "event"

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <poll.h>
#include <dirent.h>
#include <string.h>

#include <linux/input.h>

int running = 1;

static int is_event_device(const struct dirent *dir)
{
  return strncmp(EVENT_DEV_NAME, dir->d_name,
		 strlen(EVENT_DEV_NAME)-1) == 0;
}

static int open_evdev(const char *dev_name)
{
  struct dirent **namelist;
  int i, ndev;
  int fd = -1;

  ndev = scandir(DEV_INPUT_EVENT, &namelist, is_event_device, versionsort);
  if (ndev <= 0)
    return ndev;

  for (i = 0; i < ndev; i++)
    {
      char fname[64];
      char name[256];

      snprintf(fname, sizeof(fname),
	       "%s/%s", DEV_INPUT_EVENT, namelist[i]->d_name);
      fd = open(fname, O_RDONLY);
      if (fd < 0)
	continue;
      ioctl(fd, EVIOCGNAME(sizeof(name)), name);
      if (strcmp(dev_name, name) == 0)
	break;
      close(fd);
    }

  for (i = 0; i < ndev; i++)
    free(namelist[i]);

  return fd;
}

void handle_events(int evfd)
{
  struct input_event ev[64];
  int i, rd;

  rd = read(evfd, ev, sizeof(struct input_event) * 64);
  if (rd < (int) sizeof(struct input_event)) {
    fprintf(stderr, "expected %d bytes, got %d\n",
	    (int) sizeof(struct input_event), rd);
    return;
  }
  for (i = 0; i < rd / sizeof(struct input_event); i++) {
    if (ev->type != EV_KEY)
      continue;
    if (ev->value != 1)
      continue;
    switch (ev->code) {
    case KEY_ENTER:
      
      running = 0;
      break;
    case KEY_DOWN:
      printf("Key pressed\n");
      system("/sbin/poweroff");
      break;
    default:

      break;
    }
  }
}

int main(int argc, char* args[])
{
  int ret = 0;
  int fbfd = 0;
  struct pollfd evpoll = {
    .events = POLLIN,
  };
	
  evpoll.fd = open_evdev("Raspberry Pi Sense HAT Joystick");
  if (evpoll.fd < 0) {
    fprintf(stderr, "Event device not found.\n");
    return evpoll.fd;
  }

  while (running) {
    while (poll(&evpoll, 1, 0) > 0)
      handle_events(evpoll.fd);
    
    usleep (500000);
  }

  close(evpoll.fd);
  return ret;
}
