import os


#||func name=$ type=list(string)
def get_comments(path, ext):
    for _, _, filenames in os.walk(path):
        for fn in filenames:
            if fn.endswith(ext):
                for line in open(fn, "r"):
                    if line.contains("#||"):
                        yield line.split("#||", 1)


