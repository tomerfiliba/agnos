#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name = 'agnos-compiler',
    version = '1.0.0',
    description = 'Agnos Compiler Toolchain',
    author = 'Tomer Filiba',
    author_email = 'tomerf@il.ibm.com',
    maintainer = 'Tomer Filiba',
    maintainer_email = 'tomerf@il.ibm.com',
    url = 'http://agnos.sourceforge.net',
    long_description = """\
Agnos - The Agnostic RPC Framework
==================================

*Agnos* is a **cross-language**, **cross-platform**, lightweight RPC framework 
with support for passing objects *by-value* or *by-reference*. Agnos is meant 
to allow programs written in different languages to easily interoperate, 
by providing the needed bindings (glue-code) and hiding all the details from 
the programmer. The project essentially servers the same purpose as existing 
technologies like ``SOAP``, ``WSDL``, ``CORBA``, and others, but takes a 
**minimalistic approach** to the issue at hand.""",
    license = 'Apache License 2.0',
    packages = [
        'agnos_compiler',
        'agnos_compiler.compiler',
        'agnos_compiler.compiler.langs',
        'agnos_compiler.compiler.targets',
        'agnos_compiler.pysrcgen',
    ],
    package_dir = {
        'agnos_compiler' : 'src',
    },
    scripts = [
        'bin/agnosc', 
        'bin/agnosc-py'
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: C#",
        "Programming Language :: C++",
        "Programming Language :: Java",
        "Programming Language :: Python",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Object Brokering",
    ],
)


