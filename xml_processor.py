import sys
from bs4 import BeautifulSoup as bs

def myget(tag, key):
    if tag.get(key):
        return tag.get(key)
    return ""

def main(filename):
    with open(filename, "r") as file:
        bs_content = bs("".join(file.readlines()), "lxml")
        tests = bs_content.find_all("testcase")
        full_names = set()
        for test in tests:
            fn = myget(test,"file")
            cn = myget(test,"classname")
            tn = myget(test,"name")
            fullname = ""
            if cn == "":
                fullname = (fn + "::" + tn).strip()
            else:
                if cn.split('.')[-1].startswith("Test"):
                    fullname = ('/'.join(cn.split('.')[:-1]) + '.py::' + cn.split('.')[-1] + "::" + tn).strip()
                else:
                    fullname = (cn.replace('.','/') + ".py::" + tn).strip()

            if fullname in full_names:
                continue
            full_names.add(fullname)
            fullname = fullname.replace('\n', '\\n').replace(',',"{COMMA}")
            result = [fullname,test["time"]]
            if test.find("failure"):
                message = test.find("failure").get("message")
                if message and message.startswith("Failed: Timeout") and message.endswith("10.0s"):
                    result.append("timeout")
                else:
                    result.append("failure")
            elif test.find("error"):
                result.append("error")
            else:
                result.append("pass")
            print(",".join(result))


if __name__ == '__main__':
    main(sys.argv[1])
