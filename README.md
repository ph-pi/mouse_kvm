# Mouse_KVM
This utility allows you to use a dedicated mouse to control main features of a KVM.

## Features
- Change source entry when running in single source mode : single click on the button
- Go to PbP mode and select left and right sources : press the button of the left source, press the button of the right source, release buttons.
- Back from PbP to single source : double click on the button
- Swap USB entries while running PbP : single click on the right button
- Swap together left and right input sources : single click on the left button
- Wheel events are supported, but no action is associated with them at the moment.

## Requirements
- A linux OS running udev (linux > 2.6) with root privilege. Tested with Ubuntu 24.04.1 LTS under wayland and Debian GNU/Linux 11 (bookworm) on my raspberry.
- A dedicated mouse. Each button is assigned to a video source. A udev configuration is required to prevent this mouse from interfering with the graphical environment.
- Python 3.10 - No extra module to install. It could work with 3.9 but you need to remove some typehints not avalaible in 3.9.
- At least one of the computers connected to the KVM must run the script. Multiple instances is not an issue. This way, you can use your KVM even if you are not allowed to install anything on one of your computers due to privilege restrictions.
- ddcutil program

## Run it
First, you need to adjust settings (see instructions below) in the file settings.py at the root level of the project.

After, there are two options:
* Quick test : you can launch "kvm.py" (or "sudo kvm.py" if you are not menber of the ic2 group). If udev is not configured, remember that the graphical environnement and this script will both react to mouse actions. <b>Be careful where you click !</b>
* Full install : move python files in a shared folder, configure udev with instructions below (reboot needed).

## Why root privilege ?
* Using ddcutil command implies to be member of the i2c group. see https://www.ddcutil.com/i2c_permissions_using_group_i2c . By default, linux users are not members of i2c group.
* Configuring udev rules requires root privilege. 
* To copy files in /usr/local/...

# Why I wrote this tool ?
- Dell Display Manager is not available under Linux.
- Dell refuses to provide any technical information about the VCP commands of its monitors.
- I'm working with 1 Raspberry and 2 PCs connected to a DELL monitor with integrated KVM. One PC is under linux and the other one is under Windows. BUT I can't install or manage absolutly anything on this last one ! Even define an hot key is not allowed :(

In my configuration, the KVM mouse is attached to the raspberry which is the only computer permanently connected to my monitor.

# Installation
## ddcutil
ddcutil program is required. The kvm script has been tested with ddcutil version 1.4.1.
https://www.ddcutil.com/install/

## Python script
Create a folder /usr/local/mouse_kvm and copy all files with the .py extention (ddcutil.py, kvm.py, mouse.py, settings.py) to this folder. As udev configuration will impact all users, the script must be accessible for all users.
The main entry file is kvm.py .
mouse.py and ddcutil.py are two modules used by kvm.py .
settings.py contains all what you need to configure.

## Adjust your settings
### Monitor identification
```bash
ddcutil detect
```
Report "Model" to MONITOR_MODEL and "Serial number" to MONITOR_SERIAL .

### Identify the mouse device
```bash
ls /dev/input/by-id
```
You can compare the folder content when the mouse is plugged and when it is unplugged, to help you to identify the device file.
The filename should ends with "-event-mouse".

### Change VCP commands or values
VCP commands and values vary depending on the manufacturers and monitor models !

The currents settings are for a DELL U3824DW.
The best way to find the correct values, is to search in the web... As I said before, DELL refuses to provide any technical information on VCP commands.
A good start point is to search in https://github.com/ddccontrol/ddccontrol-db/tree/master/db/monitor

## UDEV configuration
You need root privilege to proceed.
Adding an udev rule addresses two points :
- Tell the graphical environnement to not manage event from this mouse as a standard mouse. Please don't move the cursor when I touch this mouse !
- Automaticaly launch the script when the dedicated mouse is dedected (on mouse pluggin event, or after a reboot). 

### Configure an udev rule for this device
You'll need to retrieve the ID_VENDOR_ID and ID_MODEL_ID values with the udevadm command using the same mouse device as that defined in the file settings.py.
```bash
udevadm info -n /dev/input/<... mouse device path> | grep "_ID"
```

Based on the template below, create the file /etc/udev/rules.d/99-mouse_kvm.rules.

Just replace the values of ID_VENDOR_ID and ID_MODEL_ID by yours and modify the path to the kvm.py if needed.
```
ACTION!="remove", KERNEL=="event[0-9]*", \
   ENV{ID_VENDOR_ID}=="413c", \
   ENV{ID_MODEL_ID}=="301a", \
   ACTION=="add", \
   ENV{LIBINPUT_IGNORE_DEVICE}="1", \
   GROUP="input", \
   RUN+="/usr/local/mouse_kvm/kvm.py"
```
Reboot the computer.

## Troubleshooting

To debug udev configuration, you can try:
```bash
udevadm control --log-priority=debug
journalctl -f
```
