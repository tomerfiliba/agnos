import os
import sys
sys.path.insert(0, os.path.abspath(".."))

from compiler import compiler
from compiler.langs import html


def link_type(tp, doc):
    BLOCK = doc.block
    TEXT = doc.text
    
    if isinstance(tp, compiler.BuiltinType):
        TEXT("<code>{0}</code>", tp.name, escape = False)
    else:
        TEXT('<a href="#{0}"><code>{0}</code></a>', tp.name, escape = False)

def docify_typedef(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = mem.name):
        with BLOCK("dl"):
            with BLOCK("dt"):
                with BLOCK("h3"):
                    TEXT("Typedef {0}", mem.name)
            with BLOCK("dd"):
                if mem.doc:
                    with BLOCK("p"):
                        TEXT("{0}", mem.doc)
                TEXT("An alias to ")
                link_type(mem.type, doc)

def docify_enum(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = mem.name):
        with BLOCK("dl"):
            with BLOCK("dt"):
                with BLOCK("h3"):
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
    with BLOCK("hr"):
        pass

def docify_record(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = mem.name):
        with BLOCK("dl"):
            with BLOCK("dt"):
                with BLOCK("h3"):
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
                                    link_type(m.type, doc)
                                    with BLOCK("b"):
                                        TEXT(m.name)
                                with BLOCK("dd"):
                                    TEXT(m.doc)
    with BLOCK("hr"):
        pass

def docify_class(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = mem.name):
        with BLOCK("dl"):
            with BLOCK("dt"):
                with BLOCK("h3"):
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
                                        link_type(m.type, doc)
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
                                        link_type(m.type, doc)
                                        with BLOCK("b"):
                                            TEXT("{0} ", m.name)
                                        TEXT("(",)
                                        for i, arg in enumerate(m.args):
                                            link_type(arg.type, doc)
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

    with BLOCK("hr"):
        pass

def docify_const(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = "_const_" + mem.name):
        with BLOCK("dl"):
            with BLOCK("dt"):
                with BLOCK("h3"):
                    TEXT(mem.name)
            with BLOCK("dd"):
                with BLOCK("p"):
                    with BLOCK("code"):
                        TEXT(repr(mem.value))
                    TEXT("(")
                    link_type(mem.type, doc)
                    TEXT(")")
                if mem.doc:
                    with BLOCK("p"):
                        TEXT(mem.doc)

def docify_func(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = "_func_" + mem.name):
        with BLOCK("dl"):
            with BLOCK("dt"):
                with BLOCK("h3"):
                    TEXT(mem.name)
                link_type(mem.type, doc)
                with BLOCK("b"):
                    TEXT("{0} ", mem.name)
                TEXT("(",)
                for i, arg in enumerate(mem.args):
                    link_type(arg.type, doc)
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
    with BLOCK("hr"):
        pass

def generic_tocer(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text
    ATTR = doc.attr
    
    link = mem.name
    if isinstance(mem, compiler.Func):
        link = "_func_" + link
    elif isinstance(mem, compiler.Const):
        link = "_const_" + link
    with BLOCK("a", href="#%s" % (link,)):
        TEXT(mem.name)

def docify(service):
    doc = html.HtmlDoc()
    BLOCK = doc.block
    TEXT = doc.text
    ATTR = doc.attr

    elements = [
        ("Typedefs", 
            [mem for mem in service.members if isinstance(mem, compiler.Typedef)],
            docify_typedef, 
            generic_tocer),
        ("Enums", 
            [mem for mem in service.members if isinstance(mem, compiler.Enum)],
            docify_enum,
            generic_tocer),
        ("Records", 
            [mem for mem in service.members if isinstance(mem, compiler.Record)],
            docify_record,
            generic_tocer),
        #("Exceptions", 
        #    [mem for mem in service.members if isinstance(mem, compiler.Exception)],
        #    docify_exception),
        ("Classes", 
            [mem for mem in service.members if isinstance(mem, compiler.Class)],
            docify_class,
            generic_tocer),
        ("Constants", 
            [mem for mem in service.members if isinstance(mem, compiler.Const)],
            docify_const,
            generic_tocer),
        ("Functions", 
            [mem for mem in service.members if isinstance(mem, compiler.Func)],
            docify_func,
            generic_tocer),
    ]
    
    with BLOCK("head"):
        with BLOCK("title"):
            TEXT("{0} Documentation", service.name)
    with BLOCK("body"):
        with BLOCK("h1"):
            TEXT("{0}", service.name)
        with BLOCK("p"):
            TEXT("{0}", service.doc)
        
        with BLOCK("dl"):
            with BLOCK("dt"):
                with BLOCK("h2"):
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
        with BLOCK("hr"):
            pass
        
        for title, members, docifier, tocer in elements:
            if not members:
                continue
            with BLOCK("dl"):
                with BLOCK("dt"):
                    with BLOCK("h2"):
                        TEXT(title)
                with BLOCK("dd"):
                    for mem in members:
                        docifier(mem, doc)
    
    return doc


def main(filename, outfile):
    service = compiler.load_spec(filename)
    doc = docify(service)
    outfile.write(doc.render())



if __name__ == "__main__":
    #filename = sys.argv[1]
    filename = "../ut/RemoteFiles.xml"
    main(filename, open("1.html", "w"))








