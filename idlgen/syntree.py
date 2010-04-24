class SourceError(Exception):
    def __init__(self, blk, msg, *args):
        self.blk = blk
        if args:
            msg %= args
        self.msg = msg
    
    def display(self):
        print "Error at %s(%d)" % (self.blk.fileinfo.filename, self.blk.lineno)
        print "    %r" % (self.blk.text)
        print self.msg


class FileInfo(object):
    def __init__(self, filename):
        self.filename = filename
        self.lines = open(filename, "r").read().splitlines()


class SourceBlock(object):
    def __init__(self, lineno, indentation, text, fileinfo):
        self.lineno = lineno
        self.fileinfo = fileinfo
        self.indentation = indentation
        self.text = text
        self.children = []
        self.stack = []
    
    def append(self, lineno, indentation, text):
        for i, blk in enumerate(self.stack):
            if blk.indentation >= indentation:
                del self.stack[i:]
                break
        parent = self.stack[-1] if self.stack else self
        child = SourceBlock(lineno, indentation, text, self.fileinfo)
        parent.children.append(child)
        self.stack.append(child)
    
    @classmethod
    def blockify_source(cls, fileinfo):
        root = cls(None, None, None, fileinfo)
        for lineno, line in enumerate(fileinfo.lines):
            line2 = line.strip()
            indentation = len(line) - len(line2)
            line = line2
            if not line.startswith("#::"):
                continue
            line = line[3:]
            line2 = line.strip()
            indentation += len(line) - len(line2)
            line = line2
            if not line:
                continue
            root.append(lineno, indentation, line)
        return root


class TokenizedBlock(object):
    def __init__(self, tag, args, doc, children, srcblock):
        self.tag = tag
        self.args = args
        self.doc = doc
        self.children = children
        self.srcblock = srcblock
    
    @classmethod
    def tokenize_block(cls, blk):
        tokens = blk.text.split()
        tag = tokens.pop(0)
        assert tag.startswith("@")
        tag = tag[1:]
        args = {}
        first = True
        while tokens:
            tok = tokens.pop(0)
            if "=" in tok:
                k, v = tok.split("=", 1)
                if not v:
                    if not tokens:
                        raise SourceError(blk, "expected '=' followed by value")
                    v = tokens.pop(0)
            elif first and (not tokens or (tokens and tokens[0] != "=")):
                k = "name"
                v = tok
            else:
                k = tok
                if not tokens:
                    raise SourceError(blk, "expected '=' followed by value")
                v = tokens.pop(0)
                if v == "=":
                    if not tokens:
                        raise SourceError(blk, "expected '=' followed by value")
                    v = tokens.pop(0)
                elif v.startswith("=") and len(v) > 1:
                    v = v[1:]
                else:
                    raise SourceError(blk, "expected '=' followed by value")
            if k in args:
                raise SourceError(blk, "argument %r given more than once", k)
            first = False
            args[k] = v
        doc = []
        children = []
        for child in blk.children:
            if child.text.startswith("@"):
                children.append(cls.tokenize_block(child))
            else:
                doc.append(child.text)
        return cls(tag, args, doc, children, blk)
    
    @classmethod
    def tokenize_root(cls, blk):
        children = []
        doc = []
        for child in blk.children:
            if child.text.startswith("@"):
                children.append(cls.tokenize_block(child))
            else:
                doc.append(child.text)
        return cls("service", dict(name="foo"), doc, children, blk)


#===============================================================================
# AST
#===============================================================================
def auto_fill_name(argname, blk):
    assert argname == "name"
    if "name" not in blk.args:
        for i in range(blk.srcblock.lineno, len(blk.srcblock.fileinfo.lines)):
            l = blk.srcblock.fileinfo.lines[i].strip()
            if l.startswith("def ") or l.startswith("class "):
                name = l.split()[1].split("(")[0]
                blk.args["name"] = name
                break
    if "name" not in blk.args:
        raise SourceError(blk.srcblock, "required argument 'name' missing and cannot be deduced")
    return blk.args["name"]

def arg_value(argname, blk):
    if argname not in blk.args:
        raise SourceError(blk.srcblock, "required argument %r missing", argname)
    return blk.args[argname]

def arg_default(default):
    def wrapper(argname, blk):
        return blk.args.get(argname, default)
    return wrapper

class AstNode(object):
    TAG = None
    CHILDREN = []
    ATTRS = {}
    
    def __init__(self, block):
        assert block.tag == self.TAG
        self.block = block
        self.doc = block.doc
        self.attrs = {}
        self.children = []
        for k, v in self.ATTRS.iteritems():
            self.attrs[k] = v(k, block)
        for arg in block.args.keys():
            if arg not in self.ATTRS:
                raise SourceError(self.block.srcblock, "invalid argument %r", arg)
        mapping = dict((cls.TAG, cls) for cls in self.CHILDREN)
        for child in block.children:
            try:
                cls = mapping[child.tag]
            except KeyError:
                raise SourceError(self.block.srcblock, "tag %r is invalid in this context", child.tag)
            self.children.append(cls(child))
    
    def display(self, level = 0):
        print "%s%s %s" % ("  " * level, self.TAG, self.attrs)
        for child in self.children:
            child.display(level + 1)
    
#    def toxml(self, level):
#        ind = "\t" * level
#        ind2 = "\t" * (level + 1)
#        attrs = " ".join('%s="%s"' % (k, v) for k, v in sorted(self.attrs.items()))
#        if self.children or self.doc:
#            lines = ["%s<%s %s>" % (ind, self.TAG, attrs)]
#            if self.doc:
#                lines.append(ind2 + "<doc>")
#                for l in self.doc:
#                    lines.append(ind2 + l)
#                lines.append(ind2 + "</doc>")
#            for child in self.children:
#                lines.append(child.toxml(level + 1))
#            lines.append("%s</%s>" % (ind, self.TAG,))
#        else:
#            lines = ["%s<%s %s/>" % (ind, self.TAG, attrs)]
#        return "\n".join(lines)

class ClassAttrNode(AstNode):
    TAG = "attr"
    ATTRS = dict(name = arg_value, type = arg_value, access = arg_default("get,set"))

class ArgNode(AstNode):
    TAG = "arg"
    ATTRS = dict(name = arg_value, type = arg_value)

class MethodNode(AstNode):
    TAG = "method"
    ATTRS = dict(name = auto_fill_name, type = arg_default("void"))
    CHILDREN = [ArgNode]

class CtorNode(AstNode):
    TAG = "ctor"
    CHILDREN = [ArgNode]

class ClassNode(AstNode):
    TAG = "class"
    ATTRS = dict(name = auto_fill_name)
    CHILDREN = [ClassAttrNode, CtorNode, MethodNode]

class FuncNode(AstNode):
    TAG = "func"
    ATTRS = dict(name = auto_fill_name, type = arg_default("void"))
    CHILDREN = [ArgNode]

class ServiceNode(AstNode):
    TAG = "service"
    ATTRS = dict(name = arg_value)
    CHILDREN = [ClassNode, FuncNode]


#===============================================================================
# API
#===============================================================================
def parse_source_file(filename):
    fileinf = FileInfo(filename)
    source_root = SourceBlock.blockify_source(fileinf)
    tokenized_root = TokenizedBlock.tokenize_root(source_root)
    ast_root = ServiceNode(tokenized_root)
    return ast_root


