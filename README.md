# Mouse_KVM
This programm drives the KVM of my DELL monitor from the three buttons of a dedicated mouse.

Why ? Two reasons :
- Dell Display Manager is not available under Linux.
- I've just received a new PC for my work but I can't install or manage absolutly anything on it ! Even define on hot key is not allowed :(


In my configuration, the mouse is attached to a raspberry which is permanently connected to my monitor.


Each of the three buttons is assigned to a specfic video input source.
- Press simultaneously 2 buttons to switch to PBP mode. The first button pressed define the left side of the PBP.
- Double click on a button to disable pbp mode and switch to the video input.
- Single click on a button commute usb ports in PBP mode


Currenly tested with Ubuntu 24.04.1 LTS under wayland and Debian GNU/Linux 11 (bullseye) on my raspberry under console mode.


STILL UNDER DEVELOPMENT but will be finished soonly (a few days)!

# install 
This script use ddcutil shell command.
https://www.ddcutil.com/install/

## Identify the mouse device
```bash
ls /dev/input/by-id
```
Plug the mouse dedicated to KVM, rerun the ls command and take one of the added files

## python script
NB : the script will be run as root => don't forget to set correctly files rights.

Recommanded install location : ...

## modify python settings file (will change to CLI parameters) : settings.py
you need to know the device file of the mouse and monitor identification information


# udev configuration
You need to have administrator privilege.

## configure udev rules for this device

udevadm -info -n <devive>

You'll need ID_VENDOR_ID and ID_MODEL_ID.

Create the file : /etc/udev/rules.d/99-mouse_kvm.rules
And replace the values of ID_VENDOR_ID and ID_MODEL_ID by yours.
```
ACTION!="remove", KERNEL=="event[0-9]*", \
   ENV{ID_VENDOR_ID}=="413c", \
   ENV{ID_MODEL_ID}=="301a", \
   ENV{LIBINPUT_IGNORE_DEVICE}="1"
   RUN+="full-path-python-kvm-script"
```
Reboot the PC.

# How to identify VCP commands and values
```bash
ddcutil -d 1 getvcp scan > /tmp/before
```
Change monitor setting with monitor buttons.
```bash
ddcutil -d 1 getvcp scan > /tmp/after
diff /tmp/before /tmp/after
```
Don't forget to set the device number (here : 1) according to your settings.
```bash
ddcutil detect
```

# To go further...
You can run multiple instances with more dedicated mouses to have more buttons, and more actions.
I think the script could be easily modified to run othen commands than ddcutil (ex: send wifi command to control led)
