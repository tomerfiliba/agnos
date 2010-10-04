#!/usr/bin/env python
import sys
import os
import shutil

shutil.rmtree("out", True)
os.mkdir("out")

for dir in ["bindings", "."]:
    for fn in os.listdir(dir):
        if not fn.endswith(".cpp"):
            continue
        infn = os.path.join(dir, fn)
        outfn = os.path.join("out", fn.replace(".cpp", ".o"))
        cmdline = "gcc -c -I../../lib/cpp/src %s -o %s" % (infn, outfn)
        print cmdline
        if os.system(cmdline) != 0:
            sys.exit(1)

os.system("cd ../../lib/cpp && ./build.py")
print "linking..."
os.system("g++ -lboost_thread -lboost_date_time -lboost_iostreams -lboost_system ../../lib/cpp/out/*.o out/*.o -o myserver")

