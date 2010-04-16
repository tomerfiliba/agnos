import os
import sys
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-o", "--out", dest="outfile",
                  help="set the output filename", 
                  metavar="FILENAME")
parser.add_option("--prefix", dest="prefix",
                  help="specify a different line prefix than the default one", 
                  metavar="PREFIX", default = "#!!")

def generate(outfile, prefix, filenames):
    lines = []
    for fn in filenames:
        lines.extend(scan(fn, prefix))
    text = "\n".join(lines)
    #open(outfile, "w").write(text)
    print text
    
if __name__ == "__main__":
    options, filenames = parser.parse_args()
    outfile = options.outfile
    if not outfile:
        outfile = "output.xml"
    
    generate(outfile, options.prefix, filenames)
