#! /usr/bin/env python3

import curses
from _curses import error as CursesError
from curses import wrapper
import textwrap
from os import environ, geteuid
import locale
import argparse

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

from host_explorer import print_host_info
from cpu_explorer import print_cpu_info
from ram_explorer import print_ram_info
from pci_explorer import print_pci_info
from net_explorer import print_nics
from sto_explorer import print_sto_info
from pow_explorer import print_total_power

def check_privileges():
    if not environ.get("SUDO_UID") and geteuid() != 0:
        raise PermissionError("You need to run this script with sudo or as root.")

check_privileges()

global MAX_ROWS, MAX_COLS
global LEGACY_BORDERS

LEGACY_BORDERS=False

curses.initscr()
if curses.has_colors():
    curses.start_color()
    curses.init_pair(1, 214, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLACK, 214)
    curses.init_pair(5, 215, curses.COLOR_BLACK)

def get_info():
    output = ""
    output += "Created by Elemento Cloud\n"
    output += "Visit www.elemento.cloud\n"
    output += "v 0.1.0\n"
    return output


def create_box(top, left, width, height, draw_border=False, title=None, fill=False, bg=None):
    global MAX_ROWS, MAX_COLS

    curses.setsyx(0, 0)

    width = int(MAX_COLS * width / 100)
    height = int(MAX_ROWS * height / 100)
    top = int(MAX_ROWS * top / 100)
    left = int(MAX_COLS * left / 100)

    if left + width > MAX_COLS:
        width = MAX_COLS - left
    if left + width == MAX_COLS - 1:
        width +=1
    if top + height > MAX_ROWS:
        height = MAX_ROWS - top

    box = curses.newwin(height,
                        width,
                        top,
                        left)
    if draw_border:
        if LEGACY_BORDERS:
            box.border('|', '|', '-', '-', '+', '+', '+', '+')
        else:
            box.border(0, 0, 0, 0, 0, 0, 0, 0)
    if title:
        box.addstr(0, 2, f" {title} ", curses.color_pair(1) | curses.A_BOLD)
    box.refresh()
    if not fill:
        der = box.derwin(height - 3, width - 5, 2, 3)
    else:
        der = box.derwin(height - 2, width -2, 1, 1)
    if bg:
        der.bkgd(' ', curses.color_pair(bg))
    return [box, der]


def print_and_format(target, index, line, header_attr=None, text_attr=None):
    skip_line = False
    if len(line) and ':' in line:
        found = line.index(':')
        is_header = False
        try:
            is_header = (line[found+1] == ' ' and line[0] != ' ')
        except IndexError:
            is_header = True
        if is_header:
            lines = line.split(':', 1)
            if len(lines) == 2:
                if not lines[1] and index > 0:
                        skip_line = True
                        lines[0] = f"\n{lines[0]}"
                target.addstr(index, 0, f"{lines[0]}:", header_attr or curses.color_pair(5))
                target.addstr(index, len(lines[0])+1, lines[1], text_attr or curses.color_pair(3))
                return skip_line
    target.addstr(index, 0, line, text_attr or curses.color_pair(3))
    return skip_line


def print_to_box(boxes, text, wrap=True, cp=None, indent_level=2):
    try:
        box = boxes[1]
        text=text.strip().rstrip()
        y, x = box.getmaxyx()
        if wrap:
            text = textwrap.fill(text, width=x -1, max_lines=y)
            i = 0
            for line in text.splitlines(True):
                print_and_format(box, i, line)
                i+=1
        else:
            text = text.splitlines(True)
            text_list = []
            for i, t in enumerate(text):
                wrapped = textwrap.wrap(t, width=x-1, break_long_words=False, subsequent_indent=" "*indent_level)
                text_list += wrapped
            i = 0
            for line in text_list:
                if i > y - 2:
                    i += print_and_format(box, i-1, f"{' '*(x-6)}[...]")
                    break
                i += print_and_format(box, i, line)
                if len(line) > x:
                    i+=1
                i+=1
        box.refresh()
    except CursesError:
        boxes[0].addstr(1, 3, "Box too small!", curses.color_pair(2))
        boxes[0].refresh()


def draw_ui(stdscr):
    host = create_box(top=0,
                      left=00,
                      width=34,
                      height=25,
                      draw_border=True,
                      title="Host info")

    cpu = create_box(top=0,
                     left=34,
                     width=36,
                     height=25,
                     draw_border=True,
                     title="CPU info")

    ram = create_box(top=0,
                     left=70,
                     width=30,
                     height=25,
                     draw_border=True,
                     title="RAM info")

    net = create_box(top=26,
                     left=0,
                     width=34,
                     height=74,
                     draw_border=True,
                     title="Network info")

    dsk = create_box(top=26,
                     left=34,
                     width=36,
                     height=74,
                     draw_border=True,
                     title="Disk info")

    pci = create_box(top=26,
                     left=70,
                     width=30,
                     height=45,
                     draw_border=True,
                     title="PCIe info")

    pow = create_box(top=70,
                     left=70,
                     width=30,
                     height=30,
                     draw_border=True,
                     title="Power info")

    items = {
        "host": host,
        "cpu": cpu,
        "ram": ram,
        "net": net,
        "dsk": dsk,
        "pci": pci,
        "pow": pow
    }

    stdscr.addstr(MAX_ROWS - 1 , 0, f" Press Q to quit. ", curses.color_pair(2))
    stdscr.addstr(MAX_ROWS - 1 , 18, f" Press R to refresh. ", curses.color_pair(1))
    stdscr.addstr(MAX_ROWS - 1 , MAX_COLS - 75, f"Shpectrometer v0.1.0 - ", curses.color_pair(1))
    stdscr.addstr(MAX_ROWS - 1 , MAX_COLS - 52, f"Created by Elemento Cloud.", curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(MAX_ROWS - 1 , MAX_COLS - 25, f"Visit www.elemento.cloud")

    return items


def print_info(items):
        
    try:
        print_to_box(items["host"], print_host_info(), wrap=False)
    except Exception as e:
        print_to_box(items["host"], f"An error occurred: {e}\n", wrap=False)
    try:
        print_to_box(items["cpu"], print_cpu_info(), wrap=False)
    except Exception as e:
        print_to_box(items["cpu"], f"An error occurred: {e}\n", wrap=False)
    try:
        print_to_box(items["ram"], print_ram_info(), wrap=False)
    except Exception as e:
        print_to_box(items["ram"], f"An error occurred: {e}\n", wrap=False)
    try:
        print_to_box(items["pci"], print_pci_info(), wrap=False)
    except Exception as e:
        print_to_box(items["pci"], f"An error occurred: {e}\n", wrap=False)
    try:
        print_to_box(items["net"], print_nics(), wrap=False)
    except Exception as e:
        print_to_box(items["net"], f"An error occurred: {e}\n", wrap=False)
    try:
        print_to_box(items["dsk"], print_sto_info(), wrap=False)
    except Exception as e:
        print_to_box(items["dsk"], f"An error occurred: {e}\n", wrap=False)
    try:
        print_to_box(items["pow"], print_total_power(), wrap=False)
    except Exception as e:
        print_to_box(items["pow"], f"An error occurred: {e}\n", wrap=False)


def main(stdscr, legacy_borders):
    global MAX_ROWS, MAX_COLS, LEGACY_BORDERS
    LEGACY_BORDERS = legacy_borders
    # curses.curs_set(0)
    stdscr.encoding = "utf_8"
    stdscr.refresh()
    MAX_ROWS, MAX_COLS = stdscr.getmaxyx()

    running = True

    try:
        items = draw_ui(stdscr=stdscr)
        print_info(items=items)
    except CursesError:
        stdscr.clear()
        stdscr.addstr(0, 0, "Terminal too small!", curses.color_pair(2))

    running = True

    while running:
        ch = stdscr.getch()
        if ch == curses.KEY_RESIZE:
            MAX_ROWS, MAX_COLS = stdscr.getmaxyx()
            curses.resizeterm(MAX_ROWS, MAX_COLS)
            stdscr.erase()
            stdscr.refresh()
            try:
                items = draw_ui(stdscr=stdscr)
                print_info(items=items)
            except CursesError:
                stdscr.clear()
                stdscr.addstr(0, 0, "Terminal too small!", curses.color_pair(2))
        elif ch == ord('q'):
            running = False
            curses.endwin()
        elif ch == ord('r'):
            print_info(items=items)
            for i in items.values():
                i[1].refresh()
        curses.doupdate()
        curses.flushinp()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Elemento Shell Meter',
                    description='A CLI utility to display system info')
    parser.add_argument('-l', '--legacy', action='store_true')
    args = parser.parse_args()
    wrapper(main, args.legacy)
