#!/usr/bin/python3

import random
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--fr", help="default 0, included", default="0", action="store")
    parser.add_argument("-t", "--to", help="default 100, not included", default="100", action="store")
    args = parser.parse_args()
    fr = int(args.fr)
    to = int(args.to)
    print(random.randint(fr, to))
