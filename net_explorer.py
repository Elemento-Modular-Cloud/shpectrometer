import subprocess
import json

CMD_LIST_NICS = r"ls -l /sys/class/net/*/device | cut -d/ -f5,13"
CMD_LINK_SPEED = "cat /sys/class/net/<INTERFACE_NAME>/speed"
CMD_IP_WRAPPER = "ip -p -j address show <INTERFACE_NAME>"
CMD_GET_BRIDGE = "bridge link show | grep <INTERFACE_NAME> | awk -F'master ' '{print $2}' | cut -d ' ' -f1"
CMD_GET_GW = "ip r | grep default | grep <IPADDR> | grep <INTERFACE_NAME>"
CMD_BMC_IP = "ipmitool lan print | grep -m 1 'IP Address[[:space:]][[:space:]]' | cut -d ':' -f2"
CMD_BMC_GW = "ipmitool lan print | grep -m 1 'Default Gateway IP' | cut -d ':' -f2"
CMD_BMC_MAC = "ipmitool lan print | grep -m 1 'MAC Address' | cut -d ':' -f2-"
CMD_BMC_MASK = "ipmitool lan print | grep -m 1 'Subnet Mask' | cut -d ':' -f2"

SPEED_LUT = {
    "-1": "Unknown",
    '100': '100Mbps',
    '1000': '1Gbps',
    '2500': '2.5Gbps',
    '5000': '5Gbps',
    '10000': '10Gbps',
    '25000': '25Gbps',
    '50000': '50Gbps',
    '100000': '100Gbps',
    '200000': '200Gbps',
    '400000': '400Gbps'
}


def get_nics():
    output = subprocess.run(CMD_LIST_NICS,
                            shell=True,
                            stdout=subprocess.PIPE)
    return output.stdout.decode().split()


def get_nic_speed(nic_name):
    result = subprocess.run(CMD_LINK_SPEED.replace("<INTERFACE_NAME>", nic_name),
                            shell=True,
                            stdout=subprocess.PIPE)
    return result.stdout.decode().split()[0]


def get_nic_gw(nic_name, ipaddr):
    result = subprocess.run(CMD_GET_GW.replace("<INTERFACE_NAME>",
                                               nic_name)\
                                      .replace("<IPADDR>",
                                               ipaddr),
                            shell=True,
                            stdout=subprocess.PIPE)
    try:
        return result.stdout.decode().split()[2]
    except IndexError:
        return None


def get_nic_master_bridge(nic_name):
    result = subprocess.run(CMD_GET_BRIDGE.replace("<INTERFACE_NAME>", nic_name),
                            shell=True,
                            stdout=subprocess.PIPE)
    return result.stdout.decode().strip()

def get_bmc_net_config():
    output = subprocess.run(CMD_BMC_IP,
                            shell=True,
                            stdout=subprocess.PIPE)
    ip = output.stdout.decode().strip()
    output = subprocess.run(CMD_BMC_GW,
                            shell=True,
                            stdout=subprocess.PIPE)
    gw = output.stdout.decode().strip()
    output = subprocess.run(CMD_BMC_MAC,
                            shell=True,
                            stdout=subprocess.PIPE)
    mac = output.stdout.decode().strip()
    output = subprocess.run(CMD_BMC_MASK,
                            shell=True,
                            stdout=subprocess.PIPE)
    mask = output.stdout.decode().strip()
    
    ret = {
            "name": "bmc",
            "mac": mac.upper(),
            "speed": "100",
            "addr": [
                {
                    "type": "ipv4",
                    "ip": ip,
                    "mask": sum(bin(int(x)).count('1') for x in mask.split('.')),
                    "gw": gw
                }
            ]
        }
    
    return ret


def get_net_config(nic_name):
    master = get_nic_master_bridge(nic_name=nic_name)
    nic_to_find = nic_name
    if master:
        nic_to_find = master
    result = subprocess.run(CMD_IP_WRAPPER.replace("<INTERFACE_NAME>", nic_to_find),
                            shell=True,
                            stdout=subprocess.PIPE)
    ip_data = json.loads(result.stdout.decode())[0]
    if "master" in ip_data:
        master = ip_data["master"]
        result = subprocess.run(CMD_IP_WRAPPER.replace("<INTERFACE_NAME>", master),
                        shell=True,
                        stdout=subprocess.PIPE)
        ip_data = json.loads(result.stdout.decode())[0]
    addr_info = ip_data["addr_info"]
    nic_config = {}
    nic_config["name"] = f"{nic_name} (part of {master})" if master else nic_name 
    nic_config["mac"] = ip_data["address"].upper()
    nic_config["addr"] = []
    for a in addr_info:
        if a["family"] == "inet":
            nic_config["addr"].append({
                "type": "ipv4",
                "ip": a["local"],
                "mask": a["prefixlen"],
                "gw": get_nic_gw(nic_name=nic_to_find, ipaddr=a["local"])
            })
        elif a["family"] == "inet6":
            nic_config["addr"].append({
                "type": "ipv6",
                "ip": a["local"],
                "mask": a["prefixlen"],
                "gw": get_nic_gw(nic_name=nic_to_find, ipaddr=a["local"])
            })
    nic_config["speed"] = get_nic_speed(nic_name=nic_name)

    return nic_config


def print_nics():
    nics = get_nics()
    nic_configs = {}
    nic_configs["bmc"] = get_bmc_net_config()
    for n in nics:
        nic_configs[n] = get_net_config(n)
    

    output = ""
    for n, nc in nic_configs.items():
        if nc["addr"]:
            addr_strs = []
            for a in nc["addr"]:
                addr_strs.append(f"{a['ip']}/{a['mask']} gateway {a.get('gw')}")
            output+=f"{nc['name']}:\n"
            output+=f"  addr: {', '.join(addr_strs)}\n"
            output+=f"  mac: {nc['mac']}\n"
            output+=f"  speed: {SPEED_LUT[nc.get('speed')]}\n"
            output+="\n"

    return output

if __name__ == "__main__":
    print(print_nics())
