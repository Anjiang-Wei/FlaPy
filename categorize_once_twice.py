import sys

def remove_suffix(s):
    if s[-5:] == "[1-2]" or s[-5:] == "[2-2]":
        return s[:-5];
    if s[-5:] == "-1-2]" or s[-5:] == "-2-2]":
        return s[:-5] + "]";
    return s

def main(filename,option):
    f=open(filename)
    lines=f.readlines()
    n=len(lines)
    tests={}
    for i in range(n):
        lines[i]=lines[i].strip()
        name=remove_suffix(",".join(lines[i].split(',')[:4]))
        if name not in tests.keys():
            tests[name] = 1
        else:
            tests[name] += 1
    for t in tests.keys():
        if tests[t] == 1 and option == "once":
            print(t)
        if tests[t] == 2 and option == "twice":
            print(t)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
