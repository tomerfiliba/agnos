from contextlib import contextmanager


class Stmt(object):
    def __init__(self, text, *args, **kwargs):
        self.colon = kwargs.pop("colon", True)
        if kwargs:
            raise TypeError("invalid keyword arguments %r" % (kwargs.keys(),))
        if args:
            text = text.format(*args)
        self.text = text
    
    def render(self):
        return [self.text + (";" if self.colon else "")]

EmptyStmt = Stmt("", colon = False)

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
        self.title = Stmt(text, *args, colon = False)
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
        if self.prefix:
            lines.append(self.prefix)
        for child in self.children:
            lines.extend("    " + l for l in child.render())
        if self.suffix:
            lines.append(self.suffix)
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
    
    STMT("using System")
    STMT("using System.Collections")
    STMT("using Thrift")
    SEP()
    with BLOCK("namespace t4"):
        with BLOCK("public class moshe"):
            with BLOCK("public moshe()"):
                STMT("int x = 5")
                STMT("int y = 6")
            SEP()
            with BLOCK("public ~moshe()"):
                STMT("Dispose(false)")
    
    print m.render()




