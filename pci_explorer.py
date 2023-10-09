import subprocess

CMD_VGA = r"lspci -nn | grep 0300" # 0300 = VGA
CMD_AUDIO = r"lspci -nn | grep 0403" # 0403 = Audio Device


def get_vgas():
    output = subprocess.run(CMD_VGA,
                            shell=True,
                            stdout=subprocess.PIPE)
    ret = output.stdout.decode().strip()
    ret = ret.replace("VGA compatible controller [0300]: ", '')
    # ret = ret.replace("Audio device [0403]:", '')
    return ret


def get_audio():
    output = subprocess.run(CMD_AUDIO,
                            shell=True,
                            stdout=subprocess.PIPE)
    return output.stdout.decode().strip()


def print_pci_info():
    output = ""
    output += f"GPUs:\n"
    for g in get_vgas().split('\n'):
        g = g.split(' ', 1)
        g = [g[0]] + g[1].rsplit('[', 1)
        if '[' in g[1]:
            g[1] = (g[1].split('[', 1))[1].rstrip('] ')
        g[2] = g[2].rsplit(']')[0]
        output += f"  {g[1]} ({g[2]}) @ {g[0]}\n"
    output += f"\n"
    output += f"Audio:\n"
    for a in get_audio().split('\n'):
        if not a:
            continue
        a = a.split(' ', 1)
        a = [a[0]] + a[1].rsplit('[', 1)
        if '[' in a[1]:
            a[1] = (a[1].split('[', 1))[1].rstrip('] ')
        a[2] = a[2].rsplit(']')[0]
        output += f"  {a[1]} ({a[2]}) @ {a[0]}\n".replace("High Definition", "HD")\
                                                 .replace("HD Audio Controller", "HD Audio")\
                                                 .replace("0403]: ", "")\
                                                 .replace("Corporation ", "")\
                                                 .replace("Advanced Micro Devices, Inc. [AMD] ", "AMD ")
    return output


if __name__ == "__main__":
    print(print_pci_info())