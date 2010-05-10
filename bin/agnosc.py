#!/usr/bin/env python
"""
agnos command-line utility
usage: 
    agnosc -t <LANG> myidl.xml
where LANG is one of
    "python", "java", "csharp", "cpp", "doc"
example:
    agnosc -t java myidl.xml
"""
import os
import sys

from optparse import OptionParser
from agnos_compiler.compiler import compile, IDLError
from agnos_compiler.compiler.targets import JavaTarget, PythonTarget, CPPTarget, CSharpTarget, DocTarget

TARGET_ALIASES = {
    "doc" : DocTarget,
    "py" : PythonTarget, 
    "python" : PythonTarget, 
    "java" : JavaTarget, 
    "csharp" : CSharpTarget,
    "c#" : CSharpTarget,
    "cs" : CSharpTarget,
    "cpp" : CPPTarget,
    "c++" : CPPTarget,
}

parser = OptionParser()
parser.add_option("-o", "--outdir", dest="outdir", default=None,
                  help="generate output into OUTDIR; the default directory used is that of the input file",  
                  metavar="OUTDIR")
parser.add_option("-t", "--target", dest="target",
                  help="specify the target output language ('python', 'java', 'csharp', 'cpp', or 'doc')", 
                  metavar="TARGET")
parser.add_option("-d", "--debug",
                  action="store_true", dest="debug", default=False,
                  help="set debug flag")

if __name__ == "__main__":
    options, args = parser.parse_args()
    args = ["../ut/RemoteFiles.xml"]
    #args = ["../srcgen/examples/mextra/mextra.xml"]
    options.target = "doc"
    if not args:
        parser.error("must specify agnos input file(s)")
    if not options.target:
        parser.error("must specify target")
    try:
        target = TARGET_ALIASES[options.target.lower()]
    except KeyError:
        parser.error("invalid target: %r" % (options.target,))
    try:
        for filename in args:
            if options.outdir:
                outdir = options.outdir
            else:
                outdir = os.path.dirname(filename)
                if not outdir:
                    outdir = "."
                outdir = os.path.join(outdir, target.DEFAULT_TARGET_DIR)
            compile(filename, target(outdir))
    except IDLError:
        raise
    except Exception, ex:
        if not options.debug:
            raise
        import pdb, sys
        print "-" * 50
        print repr(ex)
        print
        pdb.post_mortem(sys.exc_info()[2])



