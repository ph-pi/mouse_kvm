import os, fcntl, time, copy
from enum import IntEnum
from dataclasses import dataclass

from settings import DEBUG_MOUSE, DBL_CLICK_DELAY

class Event(IntEnum):
	PRESSED=0
	RELEASED=1
	MOVE=2
	CLICK=3
	DBL_CLICK=4


event_cb = [[] for _ in range(len(Event))]

@dataclass
class Props:
	x: int
	y: int
	button: int
	buttons: int
	x_overflow: bool
	y_overflow: bool

	def __init__(self, data: list):
		left_btn, right_btn, middle_btn, _, x_sign, y_sign, x_overflow, y_overflow = [(data[0] & (2**i)) != 0 for i in range(8)]
		self.buttons = data[0] & 0x7
		self.x = x_sign * -256 + data[1]
		self.y = y_sign * -256 + data[2]
		self.x_overflow=x_overflow
		self.y_overflow=y_overflow
		self.button = -1


def read_mouse(dev):
	block_mode = True
	stream = open(dev, 'rb')
	prev_buttons = 0
	click_history = [[],[],[]]

	def stream_nonblock(stream):
		global block_mode
		fcntl.fcntl(stream, fcntl.F_SETFL, fcntl.fcntl(stream, fcntl.F_GETFL) | os.O_NONBLOCK)
		block_mode = True

	def stream_block(stream):
		global block_mode
		fcntl.fcntl(stream, fcntl.F_SETFL, fcntl.fcntl(stream, fcntl.F_GETFL) & ~os.O_NONBLOCK)
		block_mode = False

	def notify(ev, props):
		if DEBUG_MOUSE: print(f'Mouse event : {ev.name} {vars(props)}')
		for cb in event_cb[ev.value]:
			cb(copy.deepcopy(props))

	try:
		while True:
			block = stream.read(3)
			t = time.time()
			if block is not None and len(block) == 3:
				props = Props(block)

				if props.x != 0 and props.y != 0:	notify(Event.MOVE, props)
				if (state_change := props.buttons ^ prev_buttons) != 0:
					prev_buttons = props.buttons
					for i, mask in enumerate([1, 2, 4]):
						if state_change & mask == 0: continue 
						props.button = i
						if props.buttons & mask == 0:  # released button
							notify(Event.RELEASED, props)
							if len(click_history[i]) == 2:
								notify(Event.DBL_CLICK, click_history[i][0]['props'])
								click_history[i] = []
							elif t - click_history[i][0]['pressed'] > DBL_CLICK_DELAY:
								notify(Event.CLICK, click_history[i][0]['props'])
								click_history[i] = []
							else:
								click_history[i][-1]['released'] = True
								stream_nonblock(stream)
						else:
							notify(Event.PRESSED, props)
							click_history[i].append(dict(pressed=t, released=False, props=copy.deepcopy(props)))

			for i in range(3):
				if len(click_history[i]) > 0 and click_history[i][0]['released'] == True and (t - click_history[i][0]['pressed']) > DBL_CLICK_DELAY:
					notify(Event.CLICK, click_history[i].pop(0)['props'])

			if block_mode == False and len(click_history[0]) + len(click_history[1]) + len(click_history[2]) == 0: stream_block(stream)

	except OSError:		
		pass
	print('Mouse KVM : lost devive. Unplugged ?')
	

def add_mouse_handler(ev: Event, fn):
	event_cb[ev.value].append(fn)