#!/bin/python3
# usage: python3 main.py <path to pattern file>
import sys
import patternCompiler as pattern
# TODO: Handle fan out

# TODO: Skip unused register in middle

# TODO: Delay the short patterns so that all the patterns have the
# same latency so it sync up with the data.
def main(argv):
    patterns=[]

    if len(argv) < 3:
        print(f"""Incorrect number of arguments
Usage: python3 {__file__} <path to pattern file> <name of component> <number of bytes per cycle>""")
        exit()

    name = argv[1]
    number_of_bytes = int(argv[2])
    if number_of_bytes != pattern.ceilToPow2(number_of_bytes):
        print("The number of bytes per cycle needs to be a power of 2")
        exit()

    with open(argv[0]) as file:
        patterns = list(file)

    pattern.main(patterns, name, number_of_bytes)

if __name__ == "__main__":
    main(sys.argv[1:])
