#!/usr/bin/env python
##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2010, Tomer Filiba (tomerf@il.ibm.com; tomerfiliba@gmail.com)
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

setup(name = 'restful_agnos',
    version = "__AGNOS_TOOLCHAIN_VERSION__",
    description = 'Agnos Compiler Toolchain',
    author = 'Tomer Filiba',
    author_email = 'tomerf@il.ibm.com',
    maintainer = 'Tomer Filiba',
    maintainer_email = 'tomerf@il.ibm.com',
    url = 'http://agnos.sourceforge.net/restful.html',
    platforms = ["POSIX", "Windows"],
    license = 'Apache License 2.0',
    packages = [
        'restful_agnos',
    ],
    package_dir = {
        'restful_agnos' : 'src',
    },
    scripts = [
        'bin/restful-agnos',
        'bin/restful-agnos.bat', 
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Object Brokering",
    ],
)


