#!/usr/bin/python3

import argparse
import time
from _datetime import datetime

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='timestamp command')
    parser.add_argument('-a', help="e.g. timestamp -a 1420000000000")
    parser.add_argument('-b', help="e.g. timestamp -b 20141231122640")

    namespace = parser.parse_args()
    if namespace.a:
        print(datetime.fromtimestamp(float(namespace.a) / 1000))
    elif namespace.b:
        print(int(time.mktime(time.strptime(namespace.b, "%Y%m%d%H%M%S")) * 1000))
    else:
        print(int(datetime.now().timestamp()) * 1000)
