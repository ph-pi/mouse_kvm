DEVICE = '/dev/input/by-id/usb-192f_USB_Optical_Mouse-event-mouse'

# You can retrive monitor informations from command : ddcutil detect
MONITOR_MODEL = "DELL U3824DW"
MONITOR_SERIAL = "2WFMZR3"

MULT_CLICK_DELAY_SEC = .400

BTN_ASSIGN: list[str] = ["0x1b", "0x0f", "0x11"]  # Left, right, middle
# Values for DELL U3824DW
#        1b: USB-C
#        0f: DisplayPort-1
#        11: HDMI-1
#        12: HDMI-2
UNPLUGED_SOURCE = "0x12"  # None = no unplugged input source - Used only to swap video inputs when VCP_SWITCH_VIDEO_INPUTS is not set

# VCP get/set commands
VCP_input_source = "0x60"  # define input source
VCP_pxp_sub_source = "0xe8"  # define the second input source
VCP_pxp_mode = "0xe9"  # define the screen sharing between the two input sources

# VCP named values
PxP_DISABLE = "0x00"
PxP_HALF = "0x24"

# VCP set only commands
VCP_SWITCH_USB = ("0xe7", "0xff00")
VCP_SWITCH_VIDEO_INPUTS = ("0xe5", "0xf001")