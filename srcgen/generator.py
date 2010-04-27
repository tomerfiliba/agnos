import os
from .syntree import parse_source_files, SourceError
from agnos_compiler.compiler.langs import python, xml
from agnos_compiler.compiler import compile
from agnos_compiler.compiler.targets import PythonTarget


class IdlGenerator(object):
    def __init__(self):
        pass
    def visit(self, root):
        root.accept(self)
    def emit_doc(self, node):
        if not node.doc:
            return
        with self.BLOCK("doc"):
            for line in node.doc:
                self.TEXT(line)
    
    def visit_RootNode(self, node):
        self.doc = xml.XmlDoc("service", name = node.service_name)
        self.ATTR = self.doc.attr
        self.BLOCK = self.doc.block
        self.TEXT = self.doc.text
        self.auto_generated_ctors = []
        self.service_name = None
        for child in node.children:
            child.accept(self)
        
        for node in self.auto_generated_ctors:
            with self.BLOCK("func", name = node.parent.attrs["name"], type = node.parent.attrs["name"]):
                if node.parent.parent.modinfo.attrs["export"]:
                    self.ATTR(package = node.parent.parent.modinfo.attrs["export"])
                self.emit_doc(node)
                for argnode in node.children:
                    with self.BLOCK("arg", name = argnode.attrs["name"], type = argnode.attrs["type"]):
                        self.emit_doc(argnode)

    def visit_ModuleNode(self, node):
        for child in node.children:
            child.accept(self)
    
    def visit_FuncNode(self, node):
        with self.BLOCK("func", name = node.attrs["name"], type = node.attrs["type"]):
            if node.parent.modinfo.attrs["export"]:
                self.ATTR(package = node.parent.modinfo.attrs["export"])
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)
    
    def visit_ClassNode(self, node):
        with self.BLOCK("class", name = node.attrs["name"]):
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
    
    def visit_CtorNode(self, node):
        self.auto_generated_ctors.append(node)
    
    def visit_FuncArgNode(self, node):
        with self.BLOCK("arg", name = node.attrs["name"], type = node.attrs["type"]):
            self.emit_doc(node)

    def visit_StructNode(self, node):
        with self.BLOCK("struct", name = node.attrs["name"]):
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)
    
    def visit_StructAttrNode(self, node):
        with self.BLOCK("attr", name = node.attrs["name"], type = node.attrs["type"]):
            self.emit_doc(node)

    def visit_ConstAttrNode(self, node):
        with self.BLOCK("const", name = node.attrs["name"], type = node.attrs["type"], value = node.attrs["value"]):
            self.emit_doc(node)


class BindingGenerator(object):
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
        for child in node.children:
            self.STMT("import {0}", child.modinfo.attrs["name"])
        self.STMT("import agnos.servers")
        self.STMT("import {0}_bindings", node.service_name)

        self.SEP()
        with self.BLOCK("class Handler({0}_bindings .IHandler)", node.service_name):
            for child in node.children:
                child.accept(self)
        self.SEP()
        with self.BLOCK("if __name__ == '__main__'"):
            self.STMT("agnos.servers.server_main({0}_bindings.Processor(Handler()))", node.service_name)
    
    def visit_FuncNode(self, node):
        args = ", ".join(arg.attrs["name"] for arg in node.children)
        with self.BLOCK("def {0}(_self, {1})", node.attrs["name"], args):
            self.STMT("return {0}.{1}({2})", node.parent.modinfo.attrs["name"], node.block.src_name, args)
    
    def visit_ClassNode(self, node):
        for child in node.children:
            child.accept(self)
    
    def visit_CtorNode(self, node):
        args = ", ".join(arg.attrs["name"] for arg in node.children)
        with self.BLOCK("def {0}(_self, {1})", node.parent.attrs["name"], args):
            self.STMT("return {0}.{1}({2})", node.parent.parent.modinfo.attrs["name"], node.parent.block.src_name, args)


def get_filenames(rootdir):
    filenames = []
    for dirpath, dirnames, fns in os.walk(rootdir):
        for fn in fns:
            if fn.endswith(".py"):
                filenames.append(os.path.join(dirpath, fn))
    return filenames


def main(rootdir, outdir = None, idlfile = None, serverfile = None):
    filenames = get_filenames(rootdir)
    try:
        ast_root = parse_source_files(filenames)
    except SourceError, ex:
        ex.display()
        raise

    if not outdir:
        outdir = rootdir
    if not idlfile:
        idlfile = os.path.join(outdir, "%s.xml" % (ast_root.service_name,))
    if not serverfile:
        serverfile = os.path.join(outdir, "%s_server.py" % (ast_root.service_name,))
    
    visitor = IdlGenerator()
    visitor.visit(ast_root)
    with open(idlfile, "w") as f:
        f.write(visitor.doc.render())
    
    compile(idlfile, PythonTarget(outdir))
    
    visitor = BindingGenerator()
    visitor.visit(ast_root)
    with open(serverfile, "w") as f:
        f.write(visitor.doc.render())
    




