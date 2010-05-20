#!/usr/bin/env python
"""
example usage:
    agnos-srcgen /path/to/my/package -o /another/path
which results in the following files under /another/path:
    * myservice.xml - the idl of myservice
    * myservice_bindings.py - agnos-generated binding code
    * myservice_server.py - executable server file
"""
import os
import sys
from optparse import OptionParser
from agnos_compiler.srcgen.generator import main 


parser = OptionParser()
parser.add_option("-o", "--outdir", dest="outdir", default=None,
                  help="generate output into OUTDIR; the default directory used is that of the input file",  
                  metavar="OUTDIR")
parser.add_option("--idlfile", dest="idlfile", default=None,
                  help="specify the generated idl file (by default, it is named as the service)", 
                  metavar="FILENAME")
parser.add_option("--serverfile", dest="serverfile", default=None,
                  help="specify the generated server file name (by default, it is named as the service, suffixed by '_server.py')", 
                  metavar="FILENAME")
parser.add_option("-r", "--rootpackage", dest="rootpackage", default=None,
                  help="specify the root package name (by default, the top directory is used)", 
                  metavar="NAME")

if __name__ == "__main__":
    options, args = parser.parse_args()
    #args = ["../srcgen/examples/mextra"]
    #options.outdir = "../srcgen/examples"
    if not args:
        parser.error("must specify agnos input file(s)")
    for fn in args:
        main(fn, outdir = options.outdir, rootpackage = options.rootpackage,
            serverfile = options.serverfile, idlfile = options.idlfile)


