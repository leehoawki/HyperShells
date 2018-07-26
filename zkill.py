#!/usr/bin/python3

import os
import sys
import argparse


def list_process(name):
    return os.popen('ps -ef | grep ' + name + ' | grep -v grep | grep -v zkill.py').read()


def kill_process(process):
    proc_id = process.split()[1]
    return os.popen("kill -9 " + proc_id).read()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="process name you want to kill.")
    parser.add_argument("-l", "--list", help="list the process you may want to kill", action="store_true")
    parser.add_argument("-a", "--all", help="kill all the process with the pattern", action="store_true")
    args = parser.parse_args()
    list = list_process(args.name)
    if args.list:
        print(list)
        sys.exit(0)
    if len(list.split("\n")) < 2:
        print("No process matches, name:" + args.name)
    elif len(list.split("\n")) == 2:
        print(kill_process(list.split("\n")[0]))
    elif len(list.split("\n")) > 2 and args.all:
        for process in list.split("\n")[:-1]:
            print(kill_process(process))
    else:
        print("Ambiguous process name:" + args.name + ", use -a to kill them all")
        print(list)
