import sys

def remove_suffix(s):
    if s[-5:] == "[1-2]" or s[-5:] == "[2-2]":
        return s[:-5];
    if s[-5:] == "-1-2]" or s[-5:] == "-2-2]":
        return s[:-5] + "]";
    return s

def main(filename):
    f = open(filename)
    for line in f.readlines():
        print(remove_suffix(",".join(line.split(",")[:4])))

if __name__ == '__main__':
    main(sys.argv[1])
