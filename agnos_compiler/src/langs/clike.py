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
from contextlib import contextmanager


class Stmt(object):
    def __init__(self, text, *args, **kwargs):
        self.suffix = kwargs.pop("suffix", ";")
        if kwargs:
            raise TypeError("invalid keyword arguments %r" % (kwargs.keys(),))
        if args:
            text = text.format(*args)
        self.text = text
    
    def render(self):
        return [self.text + self.suffix]

EmptyStmt = Stmt("", suffix = "")

class Doc(object):
    def __init__(self, text, box = False, spacer = False):
        self.box = box
        self.spacer = spacer
        self.text = text
    
    def render(self):
        lines = ["// " + l for l in self.text.splitlines()]
        if self.box:
            lines.insert(0, "//" * 39)
            lines.append("//" * 39)
        elif self.spacer:
            lines.insert(0, "//")
            lines.append("//")
        return lines 


class Block(object):
    def __init__(self, text, *args, **kwargs):
        self.prefix = kwargs.pop("prefix", "{")
        self.suffix = kwargs.pop("suffix", "}")
        if kwargs:
            raise TypeError("invalid keyword arguments %r" % (kwargs.keys(),))
        self.title = Stmt(text, *args, suffix = "")
        self.children = []
        self.stack = []
    
    def _get_head(self):
        if not self.stack:
            return self
        else:
            return self.stack[-1]

    def sep(self, count = 1):
        for i in range(count):
            self._get_head().children.append(EmptyStmt)
    def doc(self, *args, **kwargs):
        self._get_head().children.append(Doc(*args, **kwargs))
    def stmt(self, *args, **kwargs):
        self._get_head().children.append(Stmt(*args, **kwargs))
    
    @contextmanager
    def block(self, *args, **kwargs):
        blk = Block(*args, **kwargs)
        self._get_head().children.append(blk)
        self.stack.append(blk)
        yield blk
        self.stack.pop(-1)
    
    def render(self):
        lines = self.title.render()
        if self.prefix:
            lines.append(self.prefix)
        for child in self.children:
            lines.extend("\t" + l for l in child.render())
        if self.suffix:
            lines.append(self.suffix)
        return lines


class Module(Block):
    def __init__(self):
        Block.__init__(self, None)
    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        pass
    def render(self):
        lines = []
        for child in self.children:
            lines.extend(child.render())
        return "\n".join(lines)


if __name__ == "__main__":
    with Module() as m:
        BLOCK = m.block
        STMT = m.stmt
        SEP = m.sep
        
        STMT("using System")
        STMT("using System.Collections")
        STMT("using Thrift")
        SEP(2)
        with BLOCK("namespace t4"):
            with BLOCK("public class moshe"):
                STMT("private int x, y")
                SEP()
                with BLOCK("public moshe()"):
                    STMT("int x = 5")
                    STMT("int y = 6")
                SEP()
                with BLOCK("public ~moshe()"):
                    STMT("Dispose(false)")
    
    print(m.render())




