from contextlib import contextmanager


class Stmt(object):
    def __init__(self, text, *args):
        if args:
            text = text.format(*args)
        self.text = text
    def render(self):
        return [self.text]

EmptyStmt = Stmt("")

class Doc(object):
    def __init__(self, text, box = False, spacer = False):
        self.text = text
        self.box = box
        self.spacer = spacer
    def render(self):
        lines = ["# " + l for l in self.text.splitlines()]
        if self.box:
            lines.insert(0, "#" * 78)
            lines.append("#" * 78)
        elif self.spacer:
            lines.insert(0, "#")
            lines.append("#")
        return lines 

class Block(object):
    def __init__(self, text, *args, **kwargs):
        colon = kwargs.pop("colon", True)
        if kwargs:
            raise TypeError("invalid keyword arguments %r" % (kwargs.keys(),))
        if text is not None:
            self.title = Stmt(text + (":" if colon else ""), *args)
        self.children = []
        self.stack = []
    
    def _get_head(self):
        if not self.stack:
            return self
        else:
            return self.stack[-1]

    def sep(self):
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
        for child in self.children:
            lines.extend("    " + l for l in child.render())
        return lines


class Module(Block):
    def __init__(self):
        Block.__init__(self, None)
    
    def render(self):
        lines = []
        for child in self.children:
            lines.extend(child.render())
        return "\n".join(lines)


if __name__ == "__main__":
    m = Module()
    BLOCK = m.block
    STMT = m.stmt
    SEP = m.sep
    
    STMT("import sys")
    STMT("import os")
    STMT("import thrift")
    SEP()
    with BLOCK("class moshe"):
        with BLOCK("def moshe(self)"):
            STMT("self.x = 5")
            STMT("self.y = 6")
        SEP()
        with BLOCK("def foo(self)"):
            STMT("self.dispose(false)")
    
    print m.render()










