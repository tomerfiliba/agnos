from .syntree import parse_source_files, SourceError
from agnos_compiler.compiler.langs import python, xml


class IdlGenerator(object):
    def __init__(self):
        self.doc = xml.XmlDoc("service")
        self.ATTR = self.doc.attr
        self.BLOCK = self.doc.block
        self.TEXT = self.doc.text
    def visit(self, root):
        root.accept(self)
    def emit_doc(self, node):
        if not node.doc:
            return
        with self.BLOCK("doc"):
            for line in node.doc:
                self.TEXT(line)
    
    def visit_RootNode(self, node):
        self.auto_generated_ctors = []
        self.service_name = None
        for child in node.children:
            child.accept(self)
        if not self.service_name:
            raise SourceError(None, "service tag must appear once per project")
        
        self.ATTR("name", self.service_name)
        
        for node in self.auto_generated_ctors:
            with self.BLOCK("func", name = node.parent.attrs["name"], type = node.parent.attrs["name"]):
                self.emit_doc(node)
                for argnode in node.children:
                    with self.BLOCK("arg", name = argnode.attrs["name"], type = argnode.attrs["type"]):
                        self.emit_doc(argnode)
    
    def visit_ServiceNode(self, node):
        if self.service_name:
            raise SourceError(node.block.srcblock, "service tag appears more than once")
        self.service_name = node.attrs["name"]
    
    def visit_FuncNode(self, node):
        with self.BLOCK("func", name = node.attrs["name"], type = node.attrs["type"]):
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
            self.ATTR("get", "yes" if "get" in node.attrs["access"] else "no")
            self.ATTR("set", "yes" if "set" in node.attrs["access"] else "no")
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
    
    def visit_RootNode(self, node):
        self.STMT("import foo")
        self.STMT("import agnos")
        self.STMT("import agnos.servers")
        self.SEP()
        with self.BLOCK("class Handler(foo.IHandler)"):
            for child in node.children:
                child.accept(self)
        if not self.service_name:
            raise SourceError(None, "service tag must appear once per project")
        self.SEP()
        with self.BLOCK("if __name__ == '__main__'"):
            self.STMT("agnos.servers.server_main(foo.Processor(Handler()))")
    
    def visit_ServiceNode(self, node):
        if self.service_name:
            raise SourceError(node.block.srcblock, "service tag appears more than once")
        self.service_name = node.attrs["name"]
    
    def visit_FuncNode(self, node):
        args = ", ".join(arg.attrs["name"] for arg in node.children)
        with self.BLOCK("def {0}(_self, {1})", node.attrs["name"], args):
            self.STMT("pass")
    
    def visit_ClassNode(self, node):
        for child in node.children:
            child.accept(self)
    
    def visit_CtorNode(self, node):
        args = ", ".join(arg.attrs["name"] for arg in node.children)
        with self.BLOCK("def {0}(_self, {1})", node.parent.attrs["name"], args):
            self.STMT("pass")


def main(filenames):
    try:
        ast_root = parse_source_files(filenames)
        #visitor = IdlGenerator()
        #visitor.visit(ast_root)
        #print visitor.doc.render()
        
        visitor = BindingGenerator()
        visitor.visit(ast_root)
        print visitor.doc.render()
    
    except SourceError, ex:
        ex.display()




