import os
import itertools
from .syntree import parse_source_files, SourceError
from agnos_compiler.compiler.langs import python, xml
from agnos_compiler.compiler import compile
from agnos_compiler.compiler.targets import PythonTarget


ID_GENERATOR = itertools.count(200000)

class FuncInfo(object):
    def __init__(self, name, type, args, namespace = None, doc = None):
        self.name = name
        self.type = type
        self.args = args
        self.namespace = namespace
        self.doc = None


class IdlGenerator(object):
    def __init__(self):
        self.doc = xml.XmlDoc("service")
    def visit(self, root):
        root.accept(self)
    def emit_doc(self, node):
        if not node.doc:
            return
        with self.BLOCK("doc"):
            for line in node.doc:
                self.TEXT(line)
    
    def BLOCK(self, *args, **kwargs):
        kwargs["id"] = ID_GENERATOR.next()
        return self.doc.block(*args, **kwargs)
    def ATTR(self, *args, **kwargs):
        return self.doc.attr(*args, **kwargs)
    def TEXT(self, *args, **kwargs):
        return self.doc.text(*args, **kwargs)
    
    def visit_RootNode(self, node):
        self.ATTR(name = node.service_name)
        self.auto_generated_funcs = []
        self.service_name = None
        for child in node.children:
            child.accept(self)
        
        for info in self.auto_generated_funcs:
            with self.BLOCK("func", name = info.name, type = info.type):
                if info.namespace:
                    self.ATTR(namespace = info.namespace)
                self.emit_doc(info)
                for arginfo in info.args:
                    with self.BLOCK("arg", name = arginfo.attrs["name"], 
                            type = arginfo.attrs["type"]):
                        self.emit_doc(arginfo)

    def visit_ModuleNode(self, node):
        for child in node.children:
            child.accept(self)
    
    def visit_FuncNode(self, node):
        with self.BLOCK("func", name = node.attrs["name"], type = node.attrs["type"]):
            if node.parent.modinfo.attrs["namespace"]:
                self.ATTR(namespace = node.parent.modinfo.attrs["namespace"])
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)
    
    def visit_ClassNode(self, node):
        with self.BLOCK("class", name = node.attrs["name"]):
            if node.extends:
                self.ATTR(extends = ",".join(node.extends))
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)
    
    def visit_ClassAttrNode(self, node):
        with self.BLOCK("attr", name = node.attrs["name"], type = node.attrs["type"]):
            self.ATTR(get = "yes" if "get" in node.attrs["access"] else "no")
            self.ATTR(set = "yes" if "set" in node.attrs["access"] else "no")
            self.emit_doc(node)
    
    def visit_MethodArgNode(self, node):
        with self.BLOCK("arg", name = node.attrs["name"], type = node.attrs["type"]):
            self.emit_doc(node)
    
    def visit_MethodNode(self, node):
        with self.BLOCK("method", name = node.attrs["name"], type = node.attrs["type"]):
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)

    def visit_StaticMethodNode(self, node):
        self.auto_generated_funcs.append(FuncInfo(
            name = node.attrs["name"], 
            type = node.attrs["type"],
            args = node.children,
            namespace = node.parent.attrs["name"],
            doc = node.doc
            ))
    
    def visit_CtorNode(self, node):
        self.auto_generated_funcs.append(FuncInfo(
            name = "ctor", 
            type = node.parent.attrs["name"],
            args = node.children,
            namespace = node.parent.attrs["name"],
            doc = node.doc
            ))
    
    def visit_FuncArgNode(self, node):
        with self.BLOCK("arg", name = node.attrs["name"], type = node.attrs["type"]):
            self.emit_doc(node)

    def visit_RecordNode(self, node):
        with self.BLOCK("record", name = node.attrs["name"]):
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)

    def visit_ExceptionNode(self, node):
        with self.BLOCK("exception", name = node.attrs["name"]):
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)
    
    def visit_RecordAttrNode(self, node):
        with self.BLOCK("attr", name = node.attrs["name"], type = node.attrs["type"]):
            self.emit_doc(node)

    def visit_ConstNode(self, node):
        with self.BLOCK("const", name = node.attrs["name"], type = node.attrs["type"]):
            self.ATTR(value = node.attrs["value"]) 
            self.emit_doc(node)

    def visit_EnumNode(self, node):
        with self.BLOCK("enum", name = node.attrs["name"]):
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)
    
    def visit_EnumAttrNode(self, node):
        with self.BLOCK("member", name = node.attrs["name"]):
            if node.attrs["value"]:
                self.ATTR(value = node.attrs["value"])
            self.emit_doc(node)


class ServerGenerator(object):
    def __init__(self):
        self.doc = python.Module()
        self.BLOCK = self.doc.block
        self.STMT = self.doc.stmt
        self.SEP = self.doc.sep
        self.DOC = self.doc.doc
        self.service_name = None
    def visit(self, root):
        root.accept(self)
    
    def visit_ModuleNode(self, node):
        for child in node.children:
            child.accept(self)
    
    def visit_RootNode(self, node):
        self.STMT("#!/usr/bin/env python")
        self.STMT("import agnos.servers")
        self.STMT("import {0}_bindings", node.service_name)
        self.SEP()
        
        self.exception_map = {}
        self.required_modules = set()
        with self.BLOCK("class Handler({0}_bindings.IHandler)", node.service_name):
            for child in node.children:
                child.accept(self)
        self.SEP()
        
        self.DOC("required modules")
        for modname in self.required_modules:
            self.STMT("import {0}", modname)
        self.SEP()
        
        self.DOC("exception map")
        self.STMT("exception_map = {}")
        for (modname, excname), idlexc in self.exception_map.iteritems():
            self.STMT("exception_map[{0}.{1}] = {2}_bindings.{3}",
                modname, excname, node.service_name, idlexc)
        self.SEP()
        
        with self.BLOCK("if __name__ == '__main__'"):
            self.STMT("agnos.servers.server_main({0}_bindings.Processor(Handler(), exception_map))", 
                node.service_name)
        self.SEP()
    
    def visit_FuncNode(self, node):
        args = ", ".join(arg.attrs["name"] for arg in node.children)
        if "namespace" in node.attrs:
            name = node.attrs["namespace"].replace(".", "_") + "_" + node.attrs["name"]
        else:
            name = node.attrs["name"]
        with self.BLOCK("def {0}(_self, {1})", name, args):
            self.required_modules.add(node.parent.modinfo.attrs["name"])
            self.STMT("return {0}.{1}({2})", node.parent.modinfo.attrs["name"], 
                node.block.src_name, args)
    
    def visit_ExceptionNode(self, node):
        modname = node.parent.modinfo.attrs["name"]
        self.required_modules.add(modname)
        self.exception_map[(modname, node.block.src_name)] = node.attrs["name"]
    
    def visit_ClassNode(self, node):
        for child in node.children:
            child.accept(self)
    
    def visit_CtorNode(self, node):
        args = ", ".join(arg.attrs["name"] for arg in node.children)
        with self.BLOCK("def {0}_create(_self, {1})", node.parent.attrs["name"], args):
            self.required_modules.add(node.parent.modinfo.attrs["name"])
            self.STMT("return {0}.{1}({2})", node.parent.parent.modinfo.attrs["name"], 
                node.parent.block.src_name, args)

    def visit_StaticMethodNode(self, node):
        args = ", ".join(arg.attrs["name"] for arg in node.children)
        with self.BLOCK("def {0}_{1}(_self, {2})", node.parent.attrs["name"], node.attrs["name"], args):
            self.required_modules.add(node.parent.parent.modinfo.attrs["name"])
            self.STMT("return {0}.{1}.{2}({3})", node.parent.parent.modinfo.attrs["name"], 
                node.parent.block.src_name, node.block.src_name, args)


def get_filenames(rootdir, suffix = ".py"):
    if os.path.isfile(rootdir):
        filenames = [rootdir]
        rootdir = os.path.dirname(rootdir)
    else:
        filenames = []
        for dirpath, dirnames, fns in os.walk(rootdir):
            for fn in fns:
                if fn.endswith(suffix):
                    filenames.append(os.path.join(dirpath, fn))
    return filenames, rootdir


def main(rootdir, outdir = None, idlfile = None, serverfile = None, rootpackage = None):
    filenames, rootdir = get_filenames(rootdir)
    if not rootpackage:
        rootpackage = os.path.basename(rootdir)
    try:
        ast_root = parse_source_files(rootdir, filenames, rootpackage)
    except SourceError, ex:
        ex.display()
        raise

    if not outdir:
        outdir = rootdir
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    if not idlfile:
        idlfile = os.path.join(outdir, "%s.xml" % (ast_root.service_name,))
    if not serverfile:
        serverfile = os.path.join(outdir, "%s_server.py" % (ast_root.service_name,))
    
    visitor = IdlGenerator()
    visitor.visit(ast_root)
    with open(idlfile, "w") as f:
        f.write(visitor.doc.render())
    
    compile(idlfile, PythonTarget(outdir))
    
    visitor = ServerGenerator()
    visitor.visit(ast_root)
    with open(serverfile, "w") as f:
        f.write(visitor.doc.render())
    




