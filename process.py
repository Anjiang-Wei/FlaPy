import sys

def remove_suffix(s):
    if s[-5:] == "[1-2]" or s[-5:] == "[2-2]":
        return s[:-5];
    if s[-5:] == "-1-2]" or s[-5:] == "-2-2]":
        return s[:-5] + "]";
    return s

def main(filename):
    f=open(filename)
    lines=f.readlines()
    n=len(lines)
    tests = {}
    for i in range(n):
        lines[i]=lines[i].strip()
        name=remove_suffix(",".join(lines[i].split(',')[:4]))
        t=lines[i].split(',')[4]
        res=lines[i].split(',')[5]
        if name not in tests.keys():
            tests[name] = [t, res]
        elif tests[name][1] == "pass" and res != 'pass' and res != 'timeout':
            print(name,tests[name][0],tests[name][1],t,res,sep=',')

if __name__ == '__main__':
    main(sys.argv[1])
