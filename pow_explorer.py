import subprocess
from os import path
import json

CMD_TOTAL_POW = r"sudo ./total-power.sh"
with open(path.join(path.dirname(__file__), "psu_data.json")) as jsn:
    psu_data = json.load(jsn)
    PSU_MAX_POWER = psu_data.get("max_power") or ''
    PSU_EFF_CLASS = psu_data.get("efficiency_class") or ''


def get_total_power():
    try:
        output = subprocess.run(f"{CMD_TOTAL_POW} {PSU_MAX_POWER} {PSU_EFF_CLASS}",
                                cwd="/opt/elemento-power-meter",
                                shell=True,
                                stdout=subprocess.PIPE)
        return output.stdout.decode().replace('--', '')
    except FileNotFoundError:
        return "Elemento Power Meter not found!"


def print_total_power():
    pow = get_total_power()
    output = ""
    output += pow
    return output


if __name__ == "__main__":
    print(print_total_power())
