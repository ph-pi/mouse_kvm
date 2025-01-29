#!/bin/python3

from ddcutil import VCP, get_vcp, set_vcp, to_hex_string
from mouse import EVT, MouseEventManager
from settings import (
    BTN_ASSIGN,
    DEVICE,
    MULT_CLICK_DELAY_SEC,
    UNPLUGED_SOURCE,
    VCP_SWITCH_USB,
    VCP_SWITCH_VIDEO_INPUTS,
    PxP_DISABLE,
    PxP_HALF,
    VCP_input_source,
    VCP_pxp_mode,
    VCP_pxp_sub_source,
)

DEBUG = True


class MonitorState:

    def __init__(self):
        self.state = []

    def refresh(self):
        self.state = get_vcp(VCP_input_source, VCP_pxp_mode,
                             VCP_pxp_sub_source)

    def get(self, code):
        code = to_hex_string(code)
        info = [row for row in self.state if row.code == code]
        return VCP(code) if len(info) == 0 else info[0]


monitor_state = MonitorState()


def key_code_to_mouse_button_id(code):
    if 0x110 <= code <= 0x117:
        return code - 0x110
    raise Exception("the key code does not correspond to a mouse button")


def on_mouse_event(ev_type: int, ev_code: int | list[int], ev_value: int):
    if DEBUG:
        print(
            f"Mouse event : ev_type={ev_type} ev_code={ev_code} ev_value={ev_value}"
        )

    vcp_inputs = [VCP_input_source, VCP_pxp_sub_source]
    current_sources = [monitor_state.get(input).sl for input in vcp_inputs]
    current_pxp_mode = monitor_state.get(VCP_pxp_mode).sl

    match ev_type:
        case EVT.CLICK:
            match ev_value:
                case 1:  # single click
                    btn = key_code_to_mouse_button_id(ev_code)
                    if current_pxp_mode == PxP_DISABLE:
                        if DEBUG:
                            print("switch input source")
                        set_vcp(VCP_input_source,
                                BTN_ASSIGN[btn])  # Set Input Source
                    else:
                        if btn == 0:
                            if VCP_SWITCH_USB is not None:
                                if DEBUG:
                                    print("switch USB")
                                set_vcp(*VCP_SWITCH_USB)  # Set Input Source
                case 2:  # double click
                    btn = key_code_to_mouse_button_id(ev_code)
                    if DEBUG:
                        print(f"switch to unique source : {BTN_ASSIGN[btn]}")
                    set_vcp(VCP_pxp_mode, "00")  # Disable PBP
                    set_vcp(VCP_input_source,
                            BTN_ASSIGN[btn])  # Set Input Source
        case EVT.SEQ:
            if len(ev_value) == 4:  # 2 press + 2 release
                target_sources = [
                    BTN_ASSIGN[key_code_to_mouse_button_id(key)]
                    for key in ev_value if key >= 0
                ]
                if current_pxp_mode != PxP_DISABLE:
                    if (current_sources[0] == target_sources[1]
                            or current_sources[1] == target_sources[0]):
                        if VCP_SWITCH_VIDEO_INPUTS is not None:
                            set_vcp(*VCP_SWITCH_VIDEO_INPUTS)
                            current_sources.reverse()
                        elif UNPLUGED_SOURCE is not None:
                            if current_sources[0] == target_sources[1]:
                                set_vcp(VCP_input_source, UNPLUGED_SOURCE)
                                set_vcp(VCP_pxp_sub_source, target_sources[1])
                                current_sources = [
                                    UNPLUGED_SOURCE, target_sources[1]
                                ]
                            else:
                                set_vcp(VCP_pxp_sub_source, UNPLUGED_SOURCE)
                                set_vcp(VCP_input_source, target_sources[0])
                                current_sources = [
                                    target_sources[0], UNPLUGED_SOURCE
                                ]
                        else:
                            set_vcp(VCP_pxp_mode, PxP_DISABLE)  # Disable PBP
                            current_pxp_mode == PxP_DISABLE

                for vcp, curr, target in zip(vcp_inputs, current_sources,
                                             target_sources):
                    if curr != target:
                        set_vcp(vcp, target)

                if current_pxp_mode == PxP_DISABLE:
                    set_vcp(VCP_pxp_mode, PxP_HALF)
        case EVT.WHEEL:
            pass

    monitor_state.refresh()


if __name__ == "__main__":
    monitor_state.refresh()
    mem = MouseEventManager(2, MULT_CLICK_DELAY_SEC)
    mem.set_handler(on_mouse_event)
    mem.event_loop(DEVICE)
