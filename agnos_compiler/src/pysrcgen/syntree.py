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


class SourceError(Exception):
    def __init__(self, blk, msg, *args, **kwargs):
        self.blk = blk
        if args:
            msg %= args
        self.msg = msg
        self.kwargs = kwargs
    
    def display(self):
        if self.blk:
            print "Error at %s(%s)" % (self.blk.fileinfo.filename, self.blk.lineno)
            print "    %s" % (self.blk.text)
            for k, v in self.kwargs.iteritems():
                print "    %s = %r" % (k, v)
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
    
    def __str__(self):
        return "%s(%s)" % (self.fileinfo.filename, self.lineno)
    
    def append(self, lineno, indentation, text):
        for i, blk in enumerate(self.stack):
            if blk.indentation >= indentation:
                del self.stack[i:]
                break
        parent = self.stack[-1] if self.stack else self
        child = SourceBlock(lineno, indentation, text, self.fileinfo)
        parent.children.append(child)
        self.stack.append(child)
    
    def get_immediate_lines(self):
        depths = set()
        l = self.fileinfo.lines[self.lineno]
        min_ind = len(l) - len(l.lstrip())
        for i in xrange(self.lineno + 1, len(self.fileinfo.lines)):
            l = self.fileinfo.lines[i]
            l2 = l.strip()
            if not l2 or l2.startswith("#"):
                continue
            l3 = l.lstrip()
            ind = len(l) - len(l3)
            if ind < min_ind:
                break
            depths.add(ind)
            if len(depths) > 2 or ind < max(depths):
                break
            yield i, ind, l3
    
    @classmethod
    def blockify_source(cls, fileinfo):
        root = cls(None, None, None, fileinfo)
        for lineno, line in enumerate(fileinfo.lines):
            line2 = line.lstrip()
            indentation = len(line) - len(line2)
            line = line2
            if not line.startswith("#::"):
                continue
            line = line[3:]
            line2 = line.lstrip()
            indentation += len(line) - len(line2)
            line = line2
            if not line:
                continue
            root.append(lineno, indentation, line)
            #print "." * indentation + line
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
    
    def debug(self, level = 0):
        print ".." * level, self.tag, self.args
        for child in self.children:
            child.debug(level + 1)


#===============================================================================
# AST
#===============================================================================
def _get_src_name(blk):
    if blk.srcblock.lineno is None:
        return None, ()
    for i, ind, line in blk.srcblock.get_immediate_lines():
        l = line.strip()
        if l.startswith("def "):
            name = l.split()[1].split("(")[0]
            return name, ()
        elif l.startswith("class "):
            name, args = l.split()[1].split("(", 1)
            bases = [a.strip() for a in args.strip("): \t").split(",")]
            return name, bases
    return None, ()

def auto_fill_name(argname, blk):
    assert argname == "name"
    if "name" not in blk.args:
        if not blk.src_name:
            raise SourceError(blk.srcblock, "required argument 'name' missing and cannot be deduced")
        blk.args["name"] = blk.src_name
    return blk.args["name"]

def auto_enum_name(argname, blk):
    assert argname == "name"
    if argname not in blk.args:
        for i, ind, line in blk.srcblock.get_immediate_lines():
            l = line.strip()
            if "=" in l:
                n, v = l.split("=", 1)
                blk.args[argname] = n.strip()
                break
    if argname not in blk.args:
        raise SourceError(blk.srcblock, "required argument %r missing", argname)
    return blk.args[argname]

def auto_enum_value(argname, blk):
    assert argname == "value"
    if argname not in blk.args:
        for i, ind, line in blk.srcblock.get_immediate_lines():
            l = line.strip()
            if "=" in l:
                n, v = l.split("=", 1)
                blk.args[argname] = int(v.strip())
                break
    if argname not in blk.args:
        raise SourceError(blk.srcblock, "required argument %r missing", argname)
    return blk.args[argname]

def auto_const_name(argname, blk):
    assert argname == "name"
    if argname not in blk.args:
        for i, ind, line in blk.srcblock.get_immediate_lines():
            l = line.strip()
            if "=" in l:
                n, v = l.split("=", 1)
                blk.args[argname] = n.strip()
                break
    if argname not in blk.args:
        raise SourceError(blk.srcblock, "required argument %r missing", argname)
    return blk.args[argname]

def auto_const_value(argname, blk):
    assert argname == "value"
    if argname not in blk.args:
        for i, ind, line in blk.srcblock.get_immediate_lines():
            l = line.strip()
            if "=" in l:
                n, v = l.split("=", 1)
                blk.args[argname] = v.strip()
                break
    if argname not in blk.args:
        raise SourceError(blk.srcblock, "required argument %r missing", argname)
    return blk.args[argname]

def arg_value(argname, blk):
    if argname not in blk.args:
        raise SourceError(blk.srcblock, "required argument %r missing", argname)
    return blk.args[argname]

def comma_sep_arg_value(argname, blk):
    if argname not in blk.args:
        return []
    return [n.strip() for n in blk.args[argname].split(",")]

def arg_default(default, type = str):
    def wrapper(argname, blk):
        if argname not in blk.args:
            return default
        else:
            value = blk.args[argname]
            try:
                return type(value)
            except (ValueError, TypeError), ex:
                raise SourceError(blk.srcblock, "argument %r is a %s, cannot be assigned %r", argname, type.__name__, value)
    return wrapper

NOOP = lambda node: None

class AstNode(object):
    TAG = None
    CHILDREN = []
    ATTRS = {}
    GET_DOCSTRING = False
    
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
            self.block.src_name, self.block.src_bases = _get_src_name(block)
        
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
                raise SourceError(self.block.srcblock, "tag %r is invalid in this context", child.tag,
                    parent_node = self)
            self.children.append(cls2(child, self))
        
        if self.GET_DOCSTRING and not self.doc:
            self.doc = self._get_docstring(block)

    def _get_docstring(self, block):
        start_line = -1
        for i, ind, line in block.srcblock.get_immediate_lines():
            if line.startswith("'''") or line.startswith('"""'):
                start_line = i
                quote = line[:3]
                break
            elif line.startswith("'") or line.startswith('"'):
                start_line = i
                quote = line[:1]
                break
        if start_line < 0:
            return ()
        doclines = []
        for i in range(start_line, len(block.srcblock.fileinfo.lines)):
            l = block.srcblock.fileinfo.lines[i]
            l2 = l.rstrip()
            if l2.endswith(quote):
                doclines.append(l2[:-len(quote)])
                break
            else:
                doclines.append(l)
        doclines[0] = doclines[0].lstrip()[len(quote):]
        return doclines
    
    def postprocess(self):
        for child in self.children:
            child.postprocess()

    def accept(self, visitor):
        func = getattr(visitor, "visit_%s" % (self.__class__.__name__,), NOOP)
        return func(self)

class AnnotationNode(AstNode):
    TAG = "annotation"
    ATTRS = dict(name = arg_value, value = arg_value)

class ClassAttrNode(AstNode):
    TAG = "attr"
    ATTRS = dict(name = auto_fill_name, type = arg_value, access = arg_default("get,set"))

class MethodArgNode(AstNode):
    TAG = "arg"
    ATTRS = dict(name = arg_value, type = arg_value)

class MethodNode(AstNode):
    TAG = "method"
    ATTRS = dict(name = auto_fill_name, type = arg_default("void"), version = arg_default(None, int))
    CHILDREN = [MethodArgNode, AnnotationNode]
    GET_DOCSTRING = True

class StaticMethodNode(AstNode):
    TAG = "staticmethod"
    ATTRS = dict(name = auto_fill_name, type = arg_default("void"), version = arg_default(None, int))
    CHILDREN = [MethodArgNode, AnnotationNode]
    GET_DOCSTRING = True

class CtorNode(AstNode):
    TAG = "ctor"
    ATTRS = dict(version = arg_default(None, int))
    CHILDREN = [MethodArgNode, AnnotationNode]
    GET_DOCSTRING = True

def _get_versioned_members(node, members):
    for child in node.children:
        if isinstance(child, FuncNode):
            if child.parent.modinfo.attrs["namespace"]:
                name = child.parent.modinfo.attrs["namespace"] + "." + child.attrs["name"]
            else:
                name = child.attrs["name"]
        elif isinstance(child, (MethodNode, StaticMethodNode, CtorNode)):
            name = child.parent.attrs["name"] + "." + child.attrs["name"]
        else:
            continue
        
        ver = child.attrs["version"]
        if name not in members:
            members[name] = {}
        if members[name] and ver is None:
            raise SourceError(child.block.srcblock, "function %r is duplicated but not versioned. other instances: %r", name, 
                ", ".join(str(f.block.srcblock) for f in members[name].itervalues()))
        if ver in members[name]:
            raise SourceError(child.block.srcblock, "function %r is duplicated with the same version", name)
        members[name][ver] = child

class ClassNode(AstNode):
    TAG = "class"
    ATTRS = dict(name = auto_fill_name, extends = comma_sep_arg_value)
    CHILDREN = [ClassAttrNode, CtorNode, MethodNode, StaticMethodNode]
    GET_DOCSTRING = True
    
    def postprocess(self):
        members = {}
        _get_versioned_members(self, members)
        for versions in members.values():
            ordered = [n for v, n in sorted(versions.items())]
            for child in ordered:
                child.latest = False
            ordered[-1].latest = True
        AstNode.postprocess(self)

class FuncArgNode(AstNode):
    TAG = "arg"
    ATTRS = dict(name = arg_value, type = arg_value)

class FuncNode(AstNode):
    TAG = "func"
    ATTRS = dict(name = auto_fill_name, type = arg_default("void"), version = arg_default(None, int))
    CHILDREN = [FuncArgNode, AnnotationNode]
    GET_DOCSTRING = True

class ServiceNode(AstNode):
    TAG = "service"
    ATTRS = dict(name = arg_value, package = arg_default(None), versions = comma_sep_arg_value, clientversion = arg_default(None))

class ConstNode(AstNode):
    TAG = "const"
    ATTRS = dict(name = auto_const_name, type = arg_value, value = auto_const_value)

class RecordAttrNode(AstNode):
    TAG = "attr"
    ATTRS = dict(name = arg_value, type = arg_value)

class RecordNode(AstNode):
    TAG = "record"
    ATTRS = dict(name = auto_fill_name, extends = comma_sep_arg_value)
    CHILDREN = [RecordAttrNode]
    GET_DOCSTRING = True

class ExceptionNode(RecordNode):
    TAG = "exception"
    GET_DOCSTRING = True

class EnumAttrNode(AstNode):
    TAG = "member"
    ATTRS = dict(name = auto_enum_name, value = auto_enum_value)

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
    
    def postprocess(self):
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
        AstNode.postprocess(self)

class RootNode(object):
    def __init__(self, modules):
        self.service_name = None
        for module in modules:
            if module.service:
                if self.service_name:
                    raise SourceError(module.service.block.srcblock, "tag @service appears more than once per project")
                else:
                    self.service_name = module.service.attrs["name"]
                    self.package_name = module.service.attrs["package"]
                    self.supported_versions = module.service.attrs["versions"]
                    self.client_version = module.service.attrs["clientversion"]
        if not self.service_name:
            raise SourceError(None, "tag @service does not appear in project")
        self.children = modules

    def accept(self, visitor):
        func = getattr(visitor, "visit_%s" % (self.__class__.__name__,), NOOP)
        return func(self)
    
    def postprocess(self):
        classes = {}
        members = {}
        for child in self.children:
            _get_versioned_members(child, members)
            for child2 in child.children:
                if isinstance(child2, (ClassNode, ExceptionNode)):
                    classes[child2.attrs["name"]] = child2

        for cls in classes.values():
            if not cls.attrs["extends"]:
                cls.attrs["extends"] = []
                for basename in cls.block.src_bases:
                    if basename in classes:
                        cls.attrs["extends"].append(basename)
            cls.attrs["extends"] = [classes[basecls] for basecls in cls.attrs["extends"]]

        for versions in members.values():
            ordered = [n for v, n in sorted(versions.items())]
            for child in ordered:
                child.latest = False
            ordered[-1].latest = True


#===============================================================================
# API
#===============================================================================
def parse_source_file(filename):
    fileinf = FileInfo(filename)
    source_root = SourceBlock.blockify_source(fileinf)
    tokenized_root = TokenizedBlock.tokenize_root(source_root)
    #try:
    ast_root = ModuleNode(tokenized_root)
    ast_root.postprocess()
    #except Exception, ex:
    #tokenized_root.debug()
    #raise
    return ast_root

def parse_source_files(rootdir, filenames, rootpackage):
    modules = []
    if not filenames:
        raise ValueError("no source files given")
    for fn in filenames:
        ast = parse_source_file(fn)
        if not ast.children:
            continue
        if not ast.modinfo:
            relative_name = fn[len(rootdir):][:-3]
            modname = relative_name.replace("/", ".").replace("\\", ".").strip(".")
            if modname.endswith("__init__"):
                modname = modname[:-8]
            ast.modinfo = ModuleInfoNode.__new__(ModuleInfoNode)
            ast.modinfo.attrs = dict(name = rootpackage + "." + modname, namespace = None)
        modules.append(ast)
    root = RootNode(modules)
    root.postprocess()
    return root







