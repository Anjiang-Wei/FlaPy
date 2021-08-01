'''
david-time-second-2
1627724068
Project name:      accessify
Project url:       git@github.com:dmytrostriletskyi/accessify
Project hash:      6b7cf8657ffe18cd6a43c6cfb73b071084f0331e
Funcs to trace:    
Num runs:          1
david-time-second-1
1627724068
Project name:      accessify
Project url:       git@github.com:dmytrostriletskyi/accessify
Project hash:      6b7cf8657ffe18cd6a43c6cfb73b071084f0331e
Funcs to trace:    
Num runs:          1
'''
import sys
def extract(nameline, urlline, hashline):
    l1 = nameline.strip()
    l2 = urlline.strip()
    l3 = hashline.strip()
    key1 = "Project name:      "
    key2 = "Project url:       "
    key3 = "Project hash:      "
    assert key1 in l1
    assert key2 in l2
    assert key3 in l3
    return l1.replace(key1, ""), l2.replace(key2, ""), l3.replace(key3, "")

def second(line1, line2, times):
    l1 = line1.strip()
    l2 = line2.strip()
    key = "david-time-second-" + str(times)
    assert key in l1
    return int(l2)

with open("log", "r") as f:
    lines = f.readlines()
    start_time = 0
    end_time = 0
    name = ""
    url = ""
    sha = ""
    for i in range(0, len(lines)):
        if "david-time-second-1" in lines[i]:
            start_time = second(lines[i], lines[i+1], 1)
            name, url, sha = extract(lines[i+2], lines[i+3], lines[i+4])
        if "david-time-second-2" in lines[i]:
            end_time = second(lines[i], lines[i+1], 2)
            duration = end_time - start_time
            if duration >= 3600 - 10:
                print(",".join([name,url,sha,str(duration),"timeout"]), file=sys.stderr)
            print(",".join([name,url,sha,str(duration)]))
            
