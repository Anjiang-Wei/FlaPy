import sys

def main():
    projects = {}
    n = len(sys.argv) - 1
    for i in range(0,n):
        f = open(sys.argv[i+1])
        for l in f.readlines():
            proj = ",".join(l.strip().split(',')[:3])
            if proj not in projects.keys():
                projects[proj] = [0] * n
            projects[proj][i] += 1
    for proj in projects.keys():
        print(proj,",".join([ str(i) for i in projects[proj] ]),sep=',')

if __name__ == '__main__':
    main()
