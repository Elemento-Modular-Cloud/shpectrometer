import subprocess

CMD_CPU_MODEL = r"grep -m 1 'model name' /proc/cpuinfo | cut -d ':' -f2"
CMD_GET_CORES = r"lscpu | grep 'Core(s) per socket: ' | cut -d ':' -f2"
CMD_GET_THREADS = r"lscpu | grep '^CPU(s): ' | cut -d ':' -f2"
CMD_CPU_MIN_FREQ = r"lscpu | grep 'CPU min MHz' | cut -d ':' -f2"
CMD_CPU_MAX_FREQ = r"lscpu | grep 'CPU max MHz' | cut -d ':' -f2"
CMD_CPU_CUR_FREQ = r"dmidecode -t processor | grep 'Current Speed' | cut -d ':' -f2"
CMD_MANUF = r'dmidecode -t 2 | grep Manufacturer: | cut -d ":" -f2'
CMD_MODEL = r'dmidecode -t 2 | grep "Product Name:" | cut -d ":" -f2'

def get_cpu_model():
    output = subprocess.run(CMD_CPU_MODEL,
                            shell=True,
                            stdout=subprocess.PIPE)
    return output.stdout.decode().rstrip().strip()


def get_cores():
    output = subprocess.run(CMD_GET_CORES,
                            shell=True,
                            stdout=subprocess.PIPE)
    return output.stdout.decode().rstrip().strip()


def get_threads():
    output = subprocess.run(CMD_GET_THREADS,
                            shell=True,
                            stdout=subprocess.PIPE)
    return output.stdout.decode().rstrip().strip()


def get_frequency():
    min_freq = subprocess.run(CMD_CPU_MIN_FREQ,
                            shell=True,
                            stdout=subprocess.PIPE)
    min_freq = min_freq.stdout.decode().strip().rstrip()
    max_freq = subprocess.run(CMD_CPU_MAX_FREQ,
                            shell=True,
                            stdout=subprocess.PIPE)
    max_freq = max_freq.stdout.decode().strip().rstrip()
    cur_freq = subprocess.run(CMD_CPU_CUR_FREQ,
                            shell=True,
                            stdout=subprocess.PIPE)
    cur_freq = cur_freq.stdout.decode().strip().rstrip()
    output = [cur_freq, max_freq, min_freq]
    # output = [float(f) for f in output]
    # output = [f"{f/1000:.2f}GHz" if f>1000 else f"{f:.2f}MHz" for f in output]
    return output


def get_mobo_manufacturer():
    output = subprocess.run(CMD_MANUF,
                            shell=True,
                            stdout=subprocess.PIPE)
    return output.stdout.decode().rstrip().strip()


def get_mobo_model():
    output = subprocess.run(CMD_MODEL,
                            shell=True,
                            stdout=subprocess.PIPE)
    return output.stdout.decode().rstrip().strip()


def print_cpu_info():
    freq = get_frequency()
    output = ""
    output += f"Model: {get_cpu_model()}\n"
    output += f"Topology: {get_cores()} cores/{get_threads()} threads\n"
    output += f"Frequency: {freq[0]} (min. {freq[2]}, max. {freq[1]})\n"
    output += f"Motherboard model: {get_mobo_manufacturer()} {get_mobo_model()}\n"
    return output


if __name__ == "__main__":
    print(print_cpu_info())
