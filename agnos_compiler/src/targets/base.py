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
import os
from contextlib import contextmanager


class NOOP(object):
    def __enter__(self):
        pass
    def __exit__(self, *args):
        pass
NOOP = NOOP()


class TargetBase(object):
    LANGUAGE = None
    
    def __init__(self, path):
        self.path = path
        # make sure the path we're working on exists
        self.mkdir("")

    def generate(self, service):
        """implement me"""
        raise NotImplementedError()

    @contextmanager
    def new_module(self, filename):
        """creates a new module in the specified language, writing it to 
        filesystem when done without errors"""
        mod = self.LANGUAGE.Module()
        yield mod
        with self.open(filename, "w") as f:
            f.write(mod.render())
    
    def mkdir(self, name):
        """creates a relative subdirectory"""
        fullname = os.path.join(self.path, name)
        if not os.path.isdir(fullname):
            os.makedirs(fullname)
    
    def open(self, filename, mode = "w"):
        """opens a relative file"""
        return open(os.path.join(self.path, filename), mode)



