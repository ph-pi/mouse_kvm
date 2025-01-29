import fcntl
import os
import struct
import sys
import time
import types
from dataclasses import dataclass

EVT = types.SimpleNamespace(CLICK=0, SEQ=1, WHEEL=2)

EV_KEY = 0x01
EV_REL = 0x02
REL_WHEEL = 0x08

@dataclass
class Event:
    EVENT_FORMAT = "llHHI"

    event_time: int     # we use a single python int to store tv_sec & tv_usec because in Python 3, the int type has no max limit
    event_type: int
    event_code: int
    event_value: int

    def __init__(self, event_data):
        if len(event_data) == struct.calcsize(self.EVENT_FORMAT):
            (tv_sec, tv_usec, self.event_type, self.event_code, self.event_value) = (
                struct.unpack(self.EVENT_FORMAT, event_data)
            )
            self.event_time = tv_sec * 1000000 + tv_usec
        else:
            raise Exception("event_data with invalid format", event_data)


class MouseEventManager:
    """The mouse event manager class.
    """
    def __init__(self, max_clicks: int = 2, dbl_click_delay_sec: float = 0.4):
        """Mouse event manager constructor.

        Args:
            max_clicks (int): Maximum multiclicks to capture (2 for double-clicks)
            dbl_click_delay_sec (float, optional): Multi-click sequence timeout expressed in seconds. Defaults to 0.4 seconds.
        """
        self.seq: list[Event] = []
        self.max_clicks = max_clicks
        self.max_delay_usec: int = int(dbl_click_delay_sec * 1000000)
        self.has_pending_multiclick = False
        self.handler = None

    def _store_event(self, ev: Event):
        if 0 <= ev.event_value <= 1:
            self.seq.append(ev)

    def _emit(self, ev_type: int, ev_code: int, ev_value: int | list[int]):
        if self.handler:
            self.handler(ev_type, ev_code, ev_value)

    def set_handler(self, cb: callable):
        self.handler = cb

    def flush_events(self, event_time: int):
        """Emits events for all closed sequences. The event_time argument allows to detect the timemout for pending sequences (a click can no longer be transformed into a double-click)

        Args:
            event_time (int): the time used to check if pending sequence has expired
        """
        self.has_pending_multiclick = False
        if len(self.seq) > 1:
            n_consecutive = 0
            for ev in self.seq[: self.max_clicks * 2]:
                if ev.event_code != self.seq[0].event_code:
                    break
                n_consecutive += 1
            while n_consecutive > 0 and (
                len(self.seq) > n_consecutive
                or event_time - self.seq[0].event_time > self.max_delay_usec
            ):
                n = min(self.max_clicks, n_consecutive // 2)
                if n == 0:
                    break
                self._emit(EVT.CLICK, self.seq[0].event_code, n)
                n_consecutive -= n * 2
                del self.seq[: n * 2]

            self.has_pending_multiclick = n_consecutive == len(self.seq)

        if (
            len(self.seq) > 1
            and len(self.keys_pressed()) == 0
            and event_time - self.seq[0].event_time > self.max_delay_usec
        ):
            self._emit(EVT.SEQ, 0, self.keys_sequence())
            self.seq = []

    def keys_sequence(self) -> list[int]:
        """Return all key events occuring while at least one key is still pressed.

        Returns:
            list[int]: A list of key ids. A positive value means "press event", a negative value means "release event"
        """
        return [
            ev.event_code * (1 if ev.event_value == 1 else -1) for ev in self.seq
        ]

    def keys_pressed(self) -> list[int]:
        """
        Returns:
            list[int]: A list of the currently pressed keys
        """
        pressed = {}
        for ev in self.seq:
            if ev.event_value == 1:
                pressed[ev.event_code] = None
            elif ev.event_code in pressed:
                del pressed[ev.event_code]
        return list(pressed.keys())

    def on_event(self, ev: Event):
        """Input event handler

        Args:
            ev (Event): An event as defined in https://www.kernel.org/doc/Documentation/input/event-codes.txt
        """
        if ev.event_type == EV_KEY:
            self._store_event(ev)

        if ev.event_type == EV_REL and ev.event_code == REL_WHEEL:
            self.flush_events(ev.event_time + self.max_delay_usec)
            s = 1 - 2 * (ev.event_value & 0x80000000 > 0)
            self._emit(EVT.WHEEL, s, self.keys_sequence())

    def has_pending_sequence(self) -> bool:
        """
        Returns:
            bool: True when some sequences are not closed.
        """
        return self.has_pending_multiclick

    def event_loop(self, device: str):
        """Read a mouse events device file to produce custom events within an endless loop.

        Args:
            device (str): the device file (should be like "/dev/input/.../<name>-event-mouse")
        """
        try:
            with open(device, "rb") as stream:
                while True:
                    event_data = stream.read(struct.calcsize(Event.EVENT_FORMAT))
                    if event_data is not None:
                        self.on_event(Event(event_data))

                    event_time = time.time_ns() // 1000
                    self.flush_events(event_time)

                    state = fcntl.fcntl(stream, fcntl.F_GETFL)
                    if self.has_pending_sequence() == ((state & os.O_NONBLOCK) == 0):
                        fcntl.fcntl(stream, fcntl.F_SETFL, state ^ os.O_NONBLOCK)

        except OSError as e:
            print(f"Can't read device {device}: {e}")
            sys.exit(1)