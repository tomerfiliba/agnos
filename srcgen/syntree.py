import os


class SourceError(Exception):
    def __init__(self, blk, msg, *args):
        self.blk = blk
        if args:
            msg %= args
        self.msg = msg
    
    def display(self):
        if self.blk:
            print "Error at %s(%s)" % (self.blk.fileinfo.filename, self.blk.lineno)
            print "    %s" % (self.blk.text)
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
        return cls("#module-root#", {}, doc, children, blk)


#===============================================================================
# AST
#===============================================================================
def _get_src_name(blk):
    if blk.srcblock.lineno is None:
        return None
    for i in range(blk.srcblock.lineno, len(blk.srcblock.fileinfo.lines)):
        l = blk.srcblock.fileinfo.lines[i].strip()
        if l.startswith("def ") or l.startswith("class "):
            name = l.split()[1].split("(")[0]
            return  name
    return None

def auto_fill_name(argname, blk):
    assert argname == "name"
    if "name" not in blk.args:
        if not blk.src_name:
            raise SourceError(blk.srcblock, "required argument 'name' missing and cannot be deduced")
        blk.args["name"] = blk.src_name
    return blk.args["name"]

def arg_value(argname, blk):
    if argname not in blk.args:
        raise SourceError(blk.srcblock, "required argument %r missing", argname)
    return blk.args[argname]

def arg_default(default):
    def wrapper(argname, blk):
        return blk.args.get(argname, default)
    return wrapper

NOOP = lambda node: None

class AstNode(object):
    TAG = None
    CHILDREN = []
    ATTRS = {}
    
    def __init__(self, block, parent = None):
        assert block.tag == self.TAG, (block.tag, self.TAG)
        self.parent = parent
        self.block = block
        self.doc = block.doc
        self.attrs = {}
        self.children = []
        self.doc = block.doc
        
        if "srcname" in block.args:
            self.block.src_name = block.args.pop("srcname")
        elif "src_name" in block.args:
            self.block.src_name = block.args.pop("src_name")
        else:
            self.block.src_name = _get_src_name(block)
        
        for k, v in self.ATTRS.iteritems():
            self.attrs[k] = v(k, block)
        for arg in block.args.keys():
            if arg not in self.ATTRS:
                raise SourceError(self.block.srcblock, "invalid argument %r", arg)
        mapping = dict((cls2.TAG, cls2) for cls2 in self.CHILDREN)
        for child in block.children:
            try:
                cls2 = mapping[child.tag]
            except KeyError:
                raise SourceError(self.block.srcblock, "tag %r is invalid in this context", child.tag)
            self.children.append(cls2(child, self))
    
    def postprcess(self):
        for child in self.children:
            child.postprcess()

    def accept(self, visitor):
        func = getattr(visitor, "visit_%s" % (self.__class__.__name__,), NOOP)
        return func(self)

class ClassAttrNode(AstNode):
    TAG = "attr"
    ATTRS = dict(name = auto_fill_name, type = arg_value, access = arg_default("get,set"))

class MethodArgNode(AstNode):
    TAG = "arg"
    ATTRS = dict(name = arg_value, type = arg_value)

class MethodNode(AstNode):
    TAG = "method"
    ATTRS = dict(name = auto_fill_name, type = arg_default("void"))
    CHILDREN = [MethodArgNode]

class StaticMethodNode(AstNode):
    TAG = "staticmethod"
    ATTRS = dict(name = auto_fill_name, type = arg_default("void"))
    CHILDREN = [MethodArgNode]

class CtorNode(AstNode):
    TAG = "ctor"
    CHILDREN = [MethodArgNode]

class ClassNode(AstNode):
    TAG = "class"
    ATTRS = dict(name = auto_fill_name)
    CHILDREN = [ClassAttrNode, CtorNode, MethodNode, StaticMethodNode]

class FuncArgNode(AstNode):
    TAG = "arg"
    ATTRS = dict(name = arg_value, type = arg_value)

class FuncNode(AstNode):
    TAG = "func"
    ATTRS = dict(name = auto_fill_name, type = arg_default("void"))
    CHILDREN = [FuncArgNode]

class ServiceNode(AstNode):
    TAG = "service"
    ATTRS = dict(name = arg_value)

class ConstNode(AstNode):
    TAG = "const"
    ATTRS = dict(name = arg_value, type = arg_value, value = arg_value)

class RecordAttrNode(AstNode):
    TAG = "attr"
    ATTRS = dict(name = arg_value, type = arg_value)

class RecordNode(AstNode):
    TAG = "record"
    ATTRS = dict(name = auto_fill_name)
    CHILDREN = [RecordAttrNode]

class ExceptionNode(AstNode):
    TAG = "exception"
    ATTRS = dict(name = auto_fill_name)
    CHILDREN = [RecordAttrNode]

class EnumAttrNode(AstNode):
    TAG = "member"
    ATTRS = dict(name = arg_value, value = arg_default(None))

class EnumNode(AstNode):
    TAG = "enum"
    ATTRS = dict(name = auto_fill_name)
    CHILDREN = [EnumAttrNode]

class ModuleInfoNode(AstNode):
    TAG = "module"
    ATTRS = dict(name = arg_value, namespace = arg_default(None))

class ModuleNode(AstNode):
    TAG = "#module-root#"
    CHILDREN = [ClassNode, RecordNode, ExceptionNode, ConstNode, FuncNode, 
        EnumNode, ServiceNode, ModuleInfoNode]
    
    def postprcess(self):
        if not self.children:
            return
        services = [child for child in self.children if isinstance(child, ServiceNode)]
        if not services:
            self.service = None
        elif len(services) == 1:
            self.service = services[0]
        else:
            raise SourceError(services[1].block.srcblock, "tag @service must appear at most once per project")
        modinfos = [child for child in self.children if isinstance(child, ModuleInfoNode)]
        if not modinfos:
            self.modinfo = None
            #raise SourceError(self.children[0].block.srcblock, "tag @module must appear once per module")
        elif len(modinfos) == 1:
            self.modinfo = modinfos[0]
        else:
            raise SourceError(modinfos[1].block.srcblock, "tag @module must appear at most once per module")
        AstNode.postprcess(self)

class RootNode(object):
    def __init__(self, modules):
        self.service_name = None
        for module in modules:
            if module.service:
                if self.service_name:
                    raise SourceError(module.service.block.srcblock, "tag @service appears more than once per project")
                else:
                    self.service_name = module.service.attrs["name"]
        if not self.service_name:
            raise SourceError(None, "tag @service does not appear in project")
        self.children = modules

    def accept(self, visitor):
        func = getattr(visitor, "visit_%s" % (self.__class__.__name__,), NOOP)
        return func(self)

#===============================================================================
# API
#===============================================================================
def parse_source_file(filename):
    fileinf = FileInfo(filename)
    source_root = SourceBlock.blockify_source(fileinf)
    tokenized_root = TokenizedBlock.tokenize_root(source_root)
    ast_root = ModuleNode(tokenized_root)
    ast_root.postprcess()
    return ast_root

def parse_source_files(rootdir, filenames, rootpackage):
    modules = []
    for fn in filenames:
        ast = parse_source_file(fn)
        if not ast.children:
            continue
        if not ast.modinfo:
            relative_name = fn[len(rootdir):][:-3]
            modname = relative_name.replace("/", ".").replace("\\", ".").strip(".")
            ast.modinfo = ModuleInfoNode.__new__(ModuleInfoNode)
            ast.modinfo.attrs = dict(name = rootpackage + "." + modname, namespace = None)
        modules.append(ast)
    return RootNode(modules)







