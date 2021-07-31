# abagen,https://github.com/rmarkello/abagen,4af521f6d7e71d4bbebb4960ff2447256e2447eb,,,1
with open("input.csv") as f:
    lines = f.readlines()
    for line in lines:
        li = line.strip().split(",")
        li[1] = li[1].replace("https://github.com/", "git@github.com:")
        print(",".join(li))
