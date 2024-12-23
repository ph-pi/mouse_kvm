#!/bin/python3

from settings import DEBUG_KVM, BTN_ASSIGN,MONITOR_MODEL, MONITOR_SERIAL, MOUSE_DEV
from dell_vcp import VCP_FEATURE
import os, subprocess
from mouse import Event, add_mouse_handler, read_mouse


ddc_cmd_base = ['ddcutil', '-l', MONITOR_MODEL, '-n', MONITOR_SERIAL, '--brief', '--noverify']



def exec_cmd(args):	
	result = subprocess.run(args, capture_output=True, text=True)
	print(result)
	if result.returncode != 0:
		raise RuntimeError(" ".join(args), result.stderr)
	return result.stdout

def get_vcp(feature: VCP_FEATURE):
	args = ddc_cmd_base + ['getvcp', feature.value]
	print(f'EXEC ! {args}')
	try:				
		result = exec_cmd(args)
		print(f'result = {result}')
		data = result.rstrip('\n').split(' ')
		if data[0] != 'VCP': raise RuntimeError(" ".join(args), 'invalid result format')
		match data[2]:
			case 'C':
				return dict(type=data[2], current=data[3], maximum=data[4])
			case 'SNC':
				return dict(type=data[2], sl=data[3])
			case 'CNC':
				return dict(type=data[2], mh=data[3], ml=data[4], sh=data[5], sl=data[6])
			case 'T':
				return dict(type=data[2], text=data[3])
			case _:
				raise RuntimeError(" ".join(args), 'invalid result format')
	except RuntimeError as err:
		print(err.args)
		return None

def set_vcp(feature: VCP_FEATURE, value: str):
	try:
		return exec_cmd(ddc_cmd_base + ['setvcp', feature.value, value])
	except RuntimeError as err:
		print(err.args)
		return None


def dell_set_input_source(src_code):
	os.system(f"ddcutil setvcp 0x60 {hex(src_code)}")

def dell_set_pbp_mode(code):
	os.system(f"ddcutil setvcp 0xe9 {hex(code)}")

def dell_set_pip_pbp_sub(src_code):
	os.system(f"ddcutil setvcp 0xe8 {hex(src_code)}")


press_order = []

def cb_dbl_click(props):
	global press_order
	if DEBUG_KVM: print(f'single_mode {props.button}')
	set_vcp(VCP_FEATURE.pbp_mode, '00')
	set_vcp(VCP_FEATURE.input_source, BTN_ASSIGN[props.button])
	press_order = []

def cb_click(props):
	global press_order
	if len(press_order) == 1:
		if DEBUG_KVM: print(f'set_active {props.button}')

	if len(press_order) > 1:
		if DEBUG_KVM: print(f'set_pbp {press_order[0]} {press_order[1]}')
		dell_set_pbp_mode(0x0) # pbp inactive
		dell_set_input_source(BTN_ASSIGN[press_order[0]])
		dell_set_pip_pbp_sub(BTN_ASSIGN[press_order[1]])
		dell_set_pbp_mode(0x24) # pbp active

	press_order = []

def cb_pressed(props):
	global press_order
	press_order.append(props.button)


if __name__ == '__main__':
	# add_mouse_handler(Event.CLICK, cb_click)
	add_mouse_handler(Event.DBL_CLICK, cb_dbl_click)
	# add_mouse_handler(Event.PRESSED, cb_pressed)

	read_mouse(MOUSE_DEV)
