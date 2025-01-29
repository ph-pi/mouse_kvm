from dataclasses import dataclass
import subprocess
from time import monotonic_ns, sleep

from pyparsing import Optional
from settings import MONITOR_MODEL, MONITOR_SERIAL
import re

# tested with ddcutil 1.4.1

DEBUG = True
VCP_SET_INTERVAL = 0.1  # minimal delay between two VCP SET commands, expressed in seconds - Could be tuned or setted to zero
previous_set_vcp = 0

ddc_cmd_base = ["ddcutil", "-l", MONITOR_MODEL, "-n", MONITOR_SERIAL, "--brief", "--noverify"]

@dataclass
class VCP:
    """Data fields from VCP protocol."""

    code: str = ""
    type: str = ""
    current: str = None
    maximum: str = None
    mh: str = None
    ml: str = None
    sh: str = None
    sl: str = None
    text: str = None


def exec_cmd(args: list[str]) -> str:
    """Wrapper to call ddcutil with correct options and retries when fails due to "display not found" on changes impacting display driver.

    Args:
        args (list[str]): list of specific arguments to run with ddcutil.

    Raises:
        RuntimeError: Failure during shell command execution.

    Returns:
        str: stdout captured string
    """
    max_retries = 5
    while max_retries > 0:
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode == 1 and "display not found" in result.stderr.lower():
            max_retries -= 1
            print("VCP command retry")
        else:
            break

    if result.returncode != 0:
        raise RuntimeError(" ".join(args), result.stderr)
    return result.stdout


def to_hex_string(s: str) -> str:
    """
    ddutil use various format for an hex value : 0xa9 / xa9 / a9
    Format hex string into a standard format. A string starting by "0x" followed by [0-9a-f] characters.
    """
    s = re.sub("^0?x", "", s)
    return f"0x{s}".lower()


def get_vcp(*features: list[str]) -> list[VCP]:
    """Wrapper to ddcutil Get VCP command.

    Returns:
        list[VCP]: a list of VCP values returned by ddutil.
    """
    args = ddc_cmd_base + ["getvcp"] + list(features)
    if DEBUG:
        print(f"getvcp {features}")
    response = []

    try:
        result = exec_cmd(args)
        for row in result.split("\n"):
            data = row.split(" ")
            if data[0] != "VCP":
                break
            if data[2] == "C":
                response.append(
                    VCP(
                        code=to_hex_string(data[1]),
                        type="C",
                        current=to_hex_string(data[3]),
                        maximum=to_hex_string(data[4]),
                    )
                )
            if data[2] == "SNC":
                response.append(
                    VCP(
                        code=to_hex_string(data[1]),
                        type="SNC",
                        sl=to_hex_string(data[3]),
                    )
                )
            if data[2] == "CNC":
                response.append(
                    VCP(
                        code=to_hex_string(data[1]),
                        type="CNC",
                        mh=to_hex_string(data[3]),
                        ml=to_hex_string(data[4]),
                        sh=to_hex_string(data[5]),
                        sl=to_hex_string(data[6]),
                    )
                )
            if data[2] == "T":
                response.append(
                    VCP(
                        code=to_hex_string(data[1]),
                        type="T",
                        text=to_hex_string(data[3]),
                    )
                )
            
    except RuntimeError as err:
        print(err.args)

    return response


def set_vcp(feature: str, value: str) -> Optional[str]:
    """Wrapper to ddcutil Set VCP command.

    Args:
        feature (str): VCP Feature name
        value (str): Value

    Returns:
        str | None: stdout captured during ddcutil execution
    """
    global previous_set_vcp
    if DEBUG:
        print(f"setvcp {feature} {value}")

    try:
        elapsed_time = (monotonic_ns() - previous_set_vcp) / 1000000000
        if elapsed_time < VCP_SET_INTERVAL:
            sleep(VCP_SET_INTERVAL - elapsed_time)

        result = exec_cmd(ddc_cmd_base + ["setvcp", feature, value])
        previous_set_vcp = monotonic_ns()
        return result

    except RuntimeError as err:
        print(err.args)
        return None
