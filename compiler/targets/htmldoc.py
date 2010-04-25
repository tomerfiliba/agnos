from .base import TargetBase
from ..langs import xml as html
from .. import compiler
 

class DocTarget(TargetBase):
    DEFAULT_TARGET_DIR = "."
    
    def generate(self, service):
        doc = html.HtmlDoc()
        self.docify_service(service, doc)
        with self.open("%s.html" % (service.name,)) as f:
            f.write(doc.render())
    
    def docify_service(self, service, doc):
        BLOCK = doc.block
        TEXT = doc.text
    
        elements = [
            ("Typedefs", 
                [mem for mem in service.members if isinstance(mem, compiler.Typedef)],
                self.docify_typedef, 
                self.generic_tocer),
            ("Enums", 
                [mem for mem in service.members if isinstance(mem, compiler.Enum)],
                self.docify_enum,
                self.generic_tocer),
            ("Records", 
                [mem for mem in service.members if isinstance(mem, compiler.Record) 
                    and not isinstance(mem, compiler.Exception)],
                self.docify_record,
                self.generic_tocer),
            ("Exceptions", 
                [mem for mem in service.members if isinstance(mem, compiler.Exception)],
                self.docify_record,
                self.generic_tocer),
            ("Classes", 
                [mem for mem in service.members if isinstance(mem, compiler.Class)],
                self.docify_class,
                self.generic_tocer),
            ("Constants", 
                [mem for mem in service.members if isinstance(mem, compiler.Const)],
                self.docify_const,
                self.generic_tocer),
            ("Functions", 
                [mem for mem in service.members if isinstance(mem, compiler.Func)],
                self.docify_func,
                self.generic_tocer),
        ]
        
        with BLOCK("head"):
            with BLOCK("title"):
                TEXT("{0} Documentation", service.name)
        
        with BLOCK("body", style="font-family: Arial, Helvetica, sans-serif;"):
            with BLOCK("h1"):
                TEXT("{0}", service.name)
            with BLOCK("p"):
                TEXT("{0}", service.doc)
            
            self.generate_toc(elements, doc)
            
            for title, members, docifier, tocer in elements:
                if not members:
                    continue
                with BLOCK("dl"):
                    with BLOCK("dt"):
                        with BLOCK("h2", style="background-color: #CCCCFF"):
                            TEXT(title)
                    with BLOCK("dd"):
                        for mem in members:
                            docifier(mem, doc)
        
        return doc

    def generate_toc(self, elements, doc):
        BLOCK = doc.block
        TEXT = doc.text
        
        with BLOCK("dl"):
            with BLOCK("dt"):
                with BLOCK("h2", style="background-color: #CCCCFF"):
                    TEXT("Table of Contents")
            with BLOCK("dd"):
                pass
        with BLOCK("table", border="1px", cellpadding="5px", rules="rows"):
            with BLOCK("tr"):
                with BLOCK("th"):
                    TEXT("Section")
                with BLOCK("th", align="left"):
                    TEXT("Elements")
            for title, members, docifier, tocer in elements:
                if not members:
                    continue
                with BLOCK("tr"):
                    with BLOCK("td"):
                        TEXT(title)
                    with BLOCK("td"):
                        for mem in members:
                            tocer(mem, doc)
                            TEXT("&nbsp;", escape = False)
    
    def generic_tocer(self, mem, doc):
        BLOCK = doc.block
        TEXT = doc.text
        
        link = mem.name
        if isinstance(mem, compiler.Func):
            link = "_func_" + link
        elif isinstance(mem, compiler.Const):
            link = "_const_" + link
        with BLOCK("a", href="#%s" % (link,)):
            TEXT(mem.name)

    @classmethod
    def link_type(cls, tp, doc):
        BLOCK = doc.block
        TEXT = doc.text
        
        if isinstance(tp, compiler.BuiltinType):
            TEXT("<code>{0}</code>", tp.name, escape = False)
        else:
            TEXT('<a href="#{0}"><code>{0}</code></a>', tp.name, escape = False)
    
    def docify_typedef(self, mem, doc):
        BLOCK = doc.block
        TEXT = doc.text
    
        with BLOCK("a", name = mem.name):
            with BLOCK("dl"):
                with BLOCK("dt"):
                    with BLOCK("h3", style="background-color: #EEEECC"):
                        TEXT("Typedef {0}", mem.name)
                with BLOCK("dd"):
                    if mem.doc:
                        with BLOCK("p"):
                            TEXT("{0}", mem.doc)
                    TEXT("An alias to ")
                    self.link_type(mem.type, doc)
    
    def docify_enum(self, mem, doc):
        BLOCK = doc.block
        TEXT = doc.text
    
        with BLOCK("a", name = mem.name):
            with BLOCK("dl"):
                with BLOCK("dt"):
                    with BLOCK("h3", style="background-color: #EEEECC"):
                        TEXT("Enum {0}", mem.name)
                with BLOCK("dd"):
                    if mem.doc:
                        with BLOCK("p"):
                            TEXT("{0}", mem.doc)
                    with BLOCK("p"):
                        with BLOCK("h4"):
                            TEXT("Members:")
                    with BLOCK("table", border="1px", cellpadding="5px", rules="rows"):
                        with BLOCK("tr"):
                            TEXT("<th>Name</th><th>Value</th><th>Comments</th>", escape = False)
                        for m in mem.members:
                            with BLOCK("tr"):
                                with BLOCK("td"):
                                    with BLOCK("code"):
                                        TEXT(m.name)
                                with BLOCK("td"):
                                    with BLOCK("code"):
                                        TEXT(m.value)
                                with BLOCK("td"):
                                    TEXT(m.doc)
    
    def docify_record(self, mem, doc):
        BLOCK = doc.block
        TEXT = doc.text
    
        with BLOCK("a", name = mem.name):
            with BLOCK("dl"):
                with BLOCK("dt"):
                    with BLOCK("h3", style="background-color: #EEEECC"):
                        if isinstance(mem, compiler.Exception):
                            TEXT("Exception {0}", mem.name)
                        else:
                            TEXT("Record {0}", mem.name)
                with BLOCK("dd"):
                    if mem.doc:
                        with BLOCK("p"):
                            TEXT("{0}", mem.doc)
                    with BLOCK("dl"):
                        with BLOCK("dt"):
                            with BLOCK("h4"):
                                TEXT("Members:")
                        with BLOCK("dd"):
                            with BLOCK("dl"):
                                for m in mem.members:
                                    with BLOCK("dt"):
                                        self.link_type(m.type, doc)
                                        with BLOCK("b"):
                                            TEXT(m.name)
                                    with BLOCK("dd"):
                                        TEXT(m.doc)
    
    def docify_class(self, mem, doc):
        BLOCK = doc.block
        TEXT = doc.text
    
        with BLOCK("a", name = mem.name):
            with BLOCK("dl"):
                with BLOCK("dt"):
                    with BLOCK("h3", style="background-color: #EEEECC"):
                        TEXT("Class {0}", mem.name)
                with BLOCK("dd"):
                    if mem.doc:
                        with BLOCK("p"):
                            TEXT("{0}", mem.doc)
                    
                    if mem.attrs:
                        with BLOCK("dl"):
                            with BLOCK("dt"):
                                with BLOCK("h4"):
                                    TEXT("Attributes:")
                            with BLOCK("dd"):
                                with BLOCK("dl"):
                                    for m in mem.attrs:
                                        with BLOCK("dt"):
                                            self.link_type(m.type, doc)
                                            with BLOCK("b"):
                                                TEXT(m.name)
                                        with BLOCK("dd"):
                                            TEXT(m.doc)
                    
                    if mem.methods:
                        with BLOCK("dl"):
                            with BLOCK("dt"):
                                with BLOCK("h4"):
                                    TEXT("Methods:")
                            with BLOCK("dd"):
                                with BLOCK("dl"):
                                    for m in mem.methods:
                                        with BLOCK("dt"):
                                            self.link_type(m.type, doc)
                                            with BLOCK("b"):
                                                TEXT("{0} ", m.name)
                                            TEXT("(",)
                                            for i, arg in enumerate(m.args):
                                                self.link_type(arg.type, doc)
                                                TEXT("{0}", arg.name)
                                                if i < len(m.args) - 1:
                                                    TEXT(", ", arg.name)
                                            TEXT(")")
                                        with BLOCK("dd"):
                                            with BLOCK("p"):
                                                TEXT(m.doc)
                                            if m.args:
                                                with BLOCK("dl"):
                                                    with BLOCK("dt"):
                                                        with BLOCK("h5"):
                                                            TEXT("Arguments:")
                                                    with BLOCK("dd"):
                                                        with BLOCK("dl"):
                                                            for arg in m.args:
                                                                with BLOCK("dt"):
                                                                    with BLOCK("code"):
                                                                        TEXT(arg.name)
                                                                with BLOCK("dd"):
                                                                    TEXT(arg.doc)
    
    
    def docify_const(self, mem, doc):
        BLOCK = doc.block
        TEXT = doc.text
    
        with BLOCK("a", name = "_const_" + mem.name):
            with BLOCK("dl"):
                with BLOCK("dt"):
                    with BLOCK("h3", style="background-color: #EEEECC"):
                        TEXT(mem.name)
                with BLOCK("dd"):
                    with BLOCK("p"):
                        with BLOCK("code"):
                            TEXT(repr(mem.value))
                        TEXT("(")
                        self.link_type(mem.type, doc)
                        TEXT(")")
                    if mem.doc:
                        with BLOCK("p"):
                            TEXT(mem.doc)
    
    def docify_func(self, mem, doc):
        BLOCK = doc.block
        TEXT = doc.text
    
        with BLOCK("a", name = "_func_" + mem.name):
            with BLOCK("dl"):
                with BLOCK("dt"):
                    with BLOCK("h3", style="background-color: #EEEECC"):
                        TEXT(mem.name)
                    self.link_type(mem.type, doc)
                    with BLOCK("b"):
                        TEXT("{0} ", mem.name)
                    TEXT("(",)
                    for i, arg in enumerate(mem.args):
                        self.link_type(arg.type, doc)
                        TEXT("{0}", arg.name)
                        if i < len(mem.args) - 1:
                            TEXT(", ", arg.name)
                    TEXT(")")
        
                with BLOCK("dd"):
                    if mem.doc:
                        with BLOCK("p"):
                            TEXT(mem.doc)
                    
                    if mem.args:
                        with BLOCK("dl"):
                            with BLOCK("dt"):
                                TEXT("Arguments:")
                            with BLOCK("dd"):
                                with BLOCK("dl"):
                                    for arg in mem.args:
                                        with BLOCK("dt"):
                                            with BLOCK("code"):
                                                TEXT(arg.name)
                                        with BLOCK("dd"):
                                            TEXT(arg.doc)
    






