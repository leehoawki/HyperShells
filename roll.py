#!/usr/bin/python3

import random
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--fr", help="default 0, included", type=int, default=0, action="store")
    parser.add_argument("-t", "--to", help="default 100, not included", type=int, default=100, action="store")
    parser.add_argument("-c", "--count", help="default 1", type=int, default=1, action="store")
    args = parser.parse_args()
    for i in range(0, args.count):
        print(random.randint(args.fr, args.to))
