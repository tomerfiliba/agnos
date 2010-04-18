import os
import sys
sys.path.insert(0, os.path.abspath(".."))

from compiler import compiler
from compiler.langs import html


def link_type(tp, doc):
    BLOCK = doc.block
    TEXT = doc.text
    
    if isinstance(tp, compiler.BuiltinType):
        with BLOCK("code"):
            TEXT("{0}", tp.name)
    else:
        with BLOCK("a", href = "#%s" % (tp.name,)):
            with BLOCK("code"):
                TEXT("{0}", tp.name)

def docify_typedef(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = mem.name):
        with BLOCK("p"):
            with BLOCK("b"):
                TEXT("{0}", mem.name)
            TEXT("is an alias to", mem.name)
            link_type(mem.type, doc)

def docify_enum(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = mem.name):
        with BLOCK("dl"):
            with BLOCK("dt"):
                TEXT("Enum")
                with BLOCK("b"):
                    TEXT("{0}", mem.name)
                TEXT("defines the following members:")
            with BLOCK("dd"):
                with BLOCK("code"): 
                    TEXT(", ".join(m.name for m in mem.members))

def docify_record(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = mem.name):
        with BLOCK("dl"):
            with BLOCK("dt"):
                TEXT("Record ")
                with BLOCK("b"):
                    TEXT("{0}", mem.name)
                TEXT(":")
            with BLOCK("dd"):
                with BLOCK("p"):
                    TEXT("{0}", mem.doc)
                with BLOCK("p"):
                    TEXT("members:")
                with BLOCK("ul"):
                    for m in mem.members:
                        with BLOCK("li"):
                            link_type(m.type, doc)
                            TEXT("{0}: {1}", m.name, m.doc)

def docify_class(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("a", name = mem.name):
        with BLOCK("p"):
            with BLOCK("dt"):
                TEXT("Class ")
                with BLOCK("b"):
                    TEXT("{0}", mem.name)
                TEXT(":")
            with BLOCK("dd"):
                with BLOCK("p"):
                    TEXT("{0}", mem.doc)
                with BLOCK("p"):
                    TEXT("Attributes:")
                with BLOCK("ul"):
                    for attr in mem.attrs:
                        with BLOCK("li"):
                            link_type(attr.type, doc)
                            TEXT("{0}: {1}", attr.name, attr.doc)
                with BLOCK("p"):
                    TEXT("Methods:")
                    for meth in mem.methods:
                        docify_func(meth, doc)

def docify_const(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("dl"):
        with BLOCK("dt"):
            TEXT("{0} = {1}", mem.name, repr(mem.value))
        with BLOCK("dd"):
            TEXT("{0}", mem.doc)

def docify_func(mem, doc):
    BLOCK = doc.block
    TEXT = doc.text

    with BLOCK("dl"):
        with BLOCK("dt"):
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
            with BLOCK("p"):
                TEXT(mem.doc)
            with BLOCK("ul"):
                for arg in mem.args:
                    with BLOCK("li"):
                        TEXT("{0}: {1}", arg.name, arg.doc)


def docify(service):
    doc = html.HtmlDoc()
    BLOCK = doc.block
    TEXT = doc.text
    ATTR = doc.attr

    elements = [
        ("Typedefs", 
            [mem for mem in service.members if isinstance(mem, compiler.Typedef)],
            docify_typedef),
        ("Enums", 
            [mem for mem in service.members if isinstance(mem, compiler.Enum)],
            docify_enum),
        ("Records", 
            [mem for mem in service.members if isinstance(mem, compiler.Record)],
            docify_record),
        #("Exceptions", 
        #    [mem for mem in service.members if isinstance(mem, compiler.Exception)],
        #    docify_exception),
        ("Classes", 
            [mem for mem in service.members if isinstance(mem, compiler.Class)],
            docify_class),
        ("Constants", 
            [mem for mem in service.members if isinstance(mem, compiler.Const)],
            docify_const),
        ("Functions", 
            [mem for mem in service.members if isinstance(mem, compiler.Func)],
            docify_func),
    ]
    
    with BLOCK("head"):
        with BLOCK("title"):
            TEXT("{0} Documentation", service.name)
    with BLOCK("body"):
        with BLOCK("h1"):
            TEXT("{0}", service.name)
        with BLOCK("p"):
            TEXT("{0}", service.doc)
        for title, members, docifier in elements:
            if not members:
                continue
            with BLOCK("h2"):
                TEXT(title)
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








