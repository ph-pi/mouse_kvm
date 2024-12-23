DEBUG_MOUSE = False
DEBUG_KVM = True

MOUSE_DEV = "/dev/input/by-id/usb-PixArt_Dell_MS116_USB_Optical_Mouse-mouse"
DBL_CLICK_DELAY = .4

# From command : ddcutil capabilities
# Feature: 60 (Input Source)
#      Values:
#        1b: Unrecognized value
#        0f: DisplayPort-1
#        11: HDMI-1
#        12: HDMI-2
BTN_ASSIGN: list[str] = ['0x1b', '0x0f', '0x12'] # Left, right, middle

# mice stream format : https://wiki.osdev.org/Mouse_Input

# From command : ddcutil detect
MONITOR_MODEL = "DELL U3824DW"
MONITOR_SERIAL = "2WFMZR3"


