#!/usr/bin/env python

##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2011, International Business Machines Corp.
#                 Author: Tomer Filiba (tomerf@il.ibm.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name = 'agnos_compiler',
    version = "__AGNOS_TOOLCHAIN_VERSION__",
    description = 'Agnos Compiler Toolchain',
    author = 'Tomer Filiba',
    author_email = 'tomerf@il.ibm.com',
    maintainer = 'Tomer Filiba',
    maintainer_email = 'tomerf@il.ibm.com',
    url = 'http://agnos.sourceforge.net',
    platforms = ["POSIX", "Windows"],
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
        'agnos_compiler.langs',
        'agnos_compiler.targets',
        'agnos_compiler.pysrcgen',
    ],
    package_dir = {
        '' : 'src',
    },
    scripts = [
        'bin/agnosc',
        'bin/agnosc.bat', 
        'bin/agnosrc-py',
        'bin/agnosrc-py.bat',
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


