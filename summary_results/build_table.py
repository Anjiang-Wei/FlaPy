'''
slug,sha,test,Victim?,PRLink,PRStatus
git@github.com:AguaClara/aguaclara,9ee3d1d007bc984b73b19520d48954b6d81feecc,tests/core/test_cache.py::test_ac_cache,no,,clean
'''

with open("NI-status.csv", "r") as f:
    lines = f.readlines()
    inspected = fixed = nofix = na = opened = accepted = rejected = 0
    clean = pollution = random = od = capsys = 0
    alls = len(lines) - 1
    cur_projectid = 0
    cur_sha = 0
    # detected, na, submitted, accepted, rejected
    cur_info = [0, 0, 0, 0, 0]
    info = []
    for i in range(1, len(lines)):
        line = lines[i].strip()
        slug, sha, test, victim, link, status = line.split(",")
        if sha != cur_sha:
            if i != 1:
                info.append(["M" + str(cur_projectid)] + list(map(str, cur_info)))
                cur_info = [0, 0, 0, 0, 0]
            cur_projectid += 1
            cur_sha = sha
        cur_info[0] += 1
        if "N/A" in status:
            cur_info[1] += 1
        if link.startswith("http"):
            cur_info[2] += 1
            if "Accept" in status:
                cur_info[3] += 1
            if "Reject" in status:
                cur_info[4] += 1
    info.append(["M" + str(cur_projectid)] + list(map(str, cur_info)))
    print("PID,Detected,N/A,Submitted,Accepted,Rejected")
    total = [0, 0, 0, 0, 0]
    for each in info:
        print(",".join(each))
        for i in range(1, len(each)):
            total[i-1] += int(each[i])
            
    print("Total,"+ ",".join(map(str, total)))
