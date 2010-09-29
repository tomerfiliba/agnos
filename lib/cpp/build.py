#!/usr/bin/env python
import sys
import os
import shutil

shutil.rmtree("out", True)
os.mkdir("out")

for fn in os.listdir("src"):
    if not fn.endswith(".cpp"):
        continue
    infn = os.path.join("src", fn)
    outfn = os.path.join("out", fn.replace(".cpp", ".o"))
    cmdline = "gcc -c -O3 %s -o %s" % (infn, outfn)
    print cmdline
    if os.system(cmdline) != 0:
        sys.exit(1)

os.system("ar rcs libagnos.a out/*.o")
