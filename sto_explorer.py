import subprocess
from shutil import which

CMD_DEVICES = r"fdisk -l | grep 'Disk ' | grep -v 'Disk identifier:'"
CMD_GET_MD_DEVICES = r"cat /proc/mdstat | grep ' : '"
CMD_GET_MD_MEMBERS = r"mdadm -vQD <MD_NAME> | grep -o '/dev/s.*'"
CMD_GET_MD_RLEVEL = r"mdadm --detail <MD_NAME> | grep 'Raid Level : ' | cut -d ':' -f2"
CMD_GET_MODEL = r"cat /sys/class/block/<DEV_NAME>/device/model"
CMD_IS_SSD = r"cat /sys/block/<DEV_NAME>/queue/rotational"
CMD_ZPOOL_LIST = r"zpool list | grep -v '^NAME' | tr -s ' '| cut -d ' ' -f-1,2"

def get_model(dev_name):
    output = subprocess.run(CMD_GET_MODEL.replace("<DEV_NAME>", dev_name),
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if "No such file or directory" in output.stderr.decode():
        return None
    output = output.stdout.decode().strip().rstrip()
    return output


def is_ssd(dev_name):
    output = subprocess.run(CMD_IS_SSD.replace("<DEV_NAME>", dev_name),
                            shell=True,
                            stdout=subprocess.PIPE)
    output = output.stdout.decode().strip().rstrip()
    return output == "0"


def get_phys_devices():
    output = subprocess.run(CMD_DEVICES,
                            shell=True,
                            stdout=subprocess.PIPE)
    output = output.stdout.decode().splitlines()
    ret = []
    for i, l in enumerate(output):
        output[i] = [l.strip().rstrip()]
        if l.startswith("Disk /"):
            disk, rest = l.replace("Disk ", '').split(':', 1)
            size = rest.split(',', 1)[0]
            model = get_model(disk.replace("/dev/", ''))
            
            if not model:
                continue
            
            type = "Unknown"
            if is_ssd(disk.replace('/dev/','')):
                type = "SSD"
            else:
                type = "HDD"

            ret.append({
                "model": model,
                "type": type,
                "device": disk,
                "size": size.strip()
            })
        
    return ret


def get_md_devices():
    output = subprocess.run(CMD_GET_MD_DEVICES,
                            shell=True,
                            stdout=subprocess.PIPE)
    output = output.stdout.decode().splitlines()[1:]
    output = [o.split() for o in output]
    output = [{'name': o[0], 
               'mode': o[3],
               'devices': o[4:]} for o in output]
    for o in output:
        o["devices"] = [f"/dev/{d.split('[')[0]}" for d in o["devices"]]
    return output    


def get_md_members(md_name):
    output = subprocess.run(CMD_GET_MD_MEMBERS.replace("<MD_NAME>", md_name),
                            shell=True,
                            stdout=subprocess.PIPE)
    output = output.stdout.decode().splitlines()
    return output


def get_md_level(md_name):
    output = subprocess.run(CMD_GET_MD_RLEVEL.replace("<MD_NAME>", md_name),
                            shell=True,
                            stdout=subprocess.PIPE)
    output = output.stdout.decode().rstrip().strip()
    return output



def get_zfs_devices():
    if not which("zpool"):
        return []
    output = subprocess.run(CMD_ZPOOL_LIST,
                            shell=True,
                            stdout=subprocess.PIPE)
    output = output.stdout.decode().splitlines()
    ret = []
    for l in output:
        name, size = l.split(' ')
        ret.append({
            "name": name,
            "size": size
        })
    return ret


def print_sto_info():
    output = ""
    phys_devs = ""
    md_devs = ""
    zfs_devs = ""
    for d in get_phys_devices():
        phys_devs += f"  {d['model'].split('(')[0]} {d['type']} -> {d['device']} ({d['size']})\n"
    
    for d in get_md_devices():
        md_devs += f"  Linux Software RAID -> {d['name']} ({d['mode']}) -> {', '.join(d['devices'])}\n"

    for d in get_zfs_devices():
        zfs_devs += f"  ZFS Software RAID -> {d['name']} ({d['size']}) -> []\n"
    
    output += "Physical devices:\n"
    output += phys_devs
    output += "\n"
    if md_devs:
        output += "Mediated devices:\n"
        output += md_devs
        output += "\n"
    if zfs_devs:
        output += "ZFS devices:\n"
        output += zfs_devs
    return output


if __name__ == "__main__":
    print(print_sto_info())