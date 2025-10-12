#!/bin/bash
/bin/rtl_fm -f 153340000 -s 22050 | /usr/local/bin/multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -f alpha --timestamp /dev/stdin | /bin/python3 /home/pi/pagers/pager_pipe_parser.py
