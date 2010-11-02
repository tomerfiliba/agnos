##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2010, International Business Machines Corp.
#                 Author: Tomer Filiba (tomerf@il.ibm.com)
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
import itertools
from .syntree import parse_source_files, SourceError, MethodNode, ClassAttrNode
from agnos_compiler import compile
from agnos_compiler.langs import python, xml
from agnos_compiler.targets import PythonTarget


class FuncInfo(object):
    def __init__(self, name, type, args, namespace = None, doc = None, version = None, latest = True, anno = {}):
        self.name = name
        self.type = type
        self.args = args
        self.namespace = namespace
        self.doc = None
        self.version = version
        self.latest = latest
        self.anno = anno


class IdlGenerator(object):
    def __init__(self, history_file):
        self.history_file = history_file
        self.history, next_id = self.load_history()
        self._id_generator = itertools.count(next_id)
        
        self.doc = xml.XmlDoc("service")

    def load_history(self):
        history = {}
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    id, key = line.split(" ", 1)
                    history[key] = int(id)
        next_id = max(history.values()) + 1 if history else 800000
        return history, next_id

    def store_history(self):
        with open(self.history_file, "w") as f:
            for key, id in sorted(self.history.items(), key = lambda o: o[1]):
                f.write("%s %s\n" % (id, key))
    
    def visit(self, root):
        root.accept(self)
        self.store_history()

    def emit_doc(self, node):
        if not node.doc:
            return
        with self.BLOCK("doc"):
            for line in node.doc:
                self.TEXT(line)
    
    def BLOCK(self, *args, **kwargs):
        return self.doc.block(*args, **kwargs)
    def LEAF(self, *args, **kwargs):
        with self.doc.block(*args, **kwargs):
            pass
    def ATTR(self, *args, **kwargs):
        return self.doc.attr(*args, **kwargs)
    def TEXT(self, *args, **kwargs):
        return self.doc.text(*args, **kwargs)

    def get_id(self, key):
        if key not in self.history:
            self.history[key] = self._id_generator.next()
        return self.history[key]
    
    def visit_RootNode(self, node):
        self.ATTR(name = node.service_name)
        if node.package_name:
            self.ATTR(package = node.package_name)
        if node.supported_versions:
            self.ATTR(versions = ",".join(node.supported_versions))
        if node.client_version:
            self.ATTR(clientversion = node.client_version)
        
        self.auto_generated_funcs = []
        self.service_name = node.service_name
        for child in node.children:
            child.accept(self)
        
        for info in self.auto_generated_funcs:
            with self.BLOCK("func", name = info.name, type = info.type):
                if info.namespace:
                    self.ATTR(namespace = info.namespace)

                key = self.service_name + "." + info.namespace + "." + info.name
                self.ATTR(id = self.get_id(key))
                
                if not info.latest:
                    self.ATTR(clientside = "no")
                    self.ATTR(name = info.name + "_v%s" % (info.version,))

                self.emit_doc(info)
                for arginfo in info.args:
                    with self.BLOCK("arg", name = arginfo.attrs["name"], 
                            type = arginfo.attrs["type"]):
                        self.emit_doc(arginfo)

                for k, v in info.anno.iteritems():
                    with self.BLOCK("annotation", name=k, value=v):
                        pass


    def visit_ModuleNode(self, node):
        for child in node.children:
            child.accept(self)
    
    def _generate_key(self, *args):
        return self.service_name + "." + ".".join(str(a) for a in args if a)
    
    def visit_FuncNode(self, node):
        key = self._generate_key(node.parent.modinfo.attrs["namespace"], node.attrs["name"], node.attrs["version"])
        
        with self.BLOCK("func", name = node.attrs["name"], type = node.attrs["type"]):
            if node.parent.modinfo.attrs["namespace"]:
                self.ATTR(namespace = node.parent.modinfo.attrs["namespace"])
            
            if not node.latest:
                self.ATTR(clientside = "no")
                self.ATTR(name = node.attrs["name"] + "_v%s" % (node.attrs["version"],))
            
            self.ATTR(id = self.get_id(key))
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)
    
    def _get_derived_members(self, node, methods, attrs):
        for child in node.children:
            if isinstance(child, MethodNode):
                methods[child.attrs["name"]] = child 
            elif isinstance(child, ClassAttrNode):
                attrs[child.attrs["name"]] = child
        for basecls in node.attrs["extends"]:
            self._get_derived_members(basecls, methods, attrs) 
    
    def visit_ClassNode(self, node):
        with self.BLOCK("class", name = node.attrs["name"]):
            inherited_methods = {}
            inherited_attrs = {}

            if node.attrs["extends"]:
                self.ATTR(extends = ",".join(base.attrs["name"] for base in node.attrs["extends"]))
                for basecls in node.attrs["extends"]:
                    self._get_derived_members(basecls, inherited_methods, inherited_attrs)
            
            self.emit_doc(node)
            for name, method in inherited_methods.iteritems():
                key = self._generate_key(node.attrs["name"], method.attrs["name"], method.attrs["version"])
                self.LEAF("inherited-method", name = method.attrs["name"], id = self.get_id(key))

            for name, attr in inherited_attrs.iteritems():
                gkey = self._generate_key(node.attrs["name"], attr.attrs["name"], "get")
                skey = self._generate_key(node.attrs["name"], attr.attrs["name"], "set")
                self.LEAF("inherited-attr", name = attr.attrs["name"], getid = self.get_id(gkey), setid = self.get_id(skey))

            for child in node.children:
                child.accept(self)
    
    def visit_ClassAttrNode(self, node):
        with self.BLOCK("attr", name = node.attrs["name"], type = node.attrs["type"]):
            if "get" in node.attrs["access"]:
                key = self._generate_key(node.parent.attrs["name"], node.attrs["name"], "get")
                self.ATTR(getid = self.get_id(key))
            if "set" in node.attrs["access"]:
                key = self._generate_key(node.parent.attrs["name"], node.attrs["name"], "set")
                self.ATTR(setid = self.get_id(key))
            
            self.ATTR(get = "yes" if "get" in node.attrs["access"] else "no")
            self.ATTR(set = "yes" if "set" in node.attrs["access"] else "no")
            self.emit_doc(node)
    
    def visit_MethodArgNode(self, node):
        with self.BLOCK("arg", name = node.attrs["name"], type = node.attrs["type"]):
            self.emit_doc(node)
    
    def visit_MethodNode(self, node):
        key = self._generate_key(node.parent.attrs["name"], node.attrs["name"], node.attrs["version"])

        with self.BLOCK("method", name = node.attrs["name"], type = node.attrs["type"]):
            if not node.latest:
                self.ATTR(clientside = "no")
                self.ATTR(name = node.attrs["name"] + "_v%s" % (node.attrs["version"],))

            self.ATTR(id = self.get_id(key))
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)

    def visit_StaticMethodNode(self, node):
        self.auto_generated_funcs.append(FuncInfo(
            name = node.attrs["name"], 
            type = node.attrs["type"],
            args = node.children,
            namespace = node.parent.attrs["name"],
            doc = node.doc,
            version = node.attrs["version"],
            latest = node.latest,
            anno = dict(info = "static_method"),
            ))
    
    def visit_CtorNode(self, node):
        self.auto_generated_funcs.append(FuncInfo(
            name = "ctor", 
            type = node.parent.attrs["name"],
            args = node.children,
            namespace = node.parent.attrs["name"],
            doc = node.doc,
            version = node.attrs["version"],
            latest = node.latest,
            anno = dict(info = "ctor_method"),
            ))
    
    def visit_FuncArgNode(self, node):
        with self.BLOCK("arg", name = node.attrs["name"], type = node.attrs["type"]):
            self.emit_doc(node)

    def visit_RecordNode(self, node):
        with self.BLOCK("record", name = node.attrs["name"]):
            if node.attrs["extends"]:
                self.ATTR(extends = ",".join(base.attrs["name"] for base in node.attrs["extends"]))
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)

    def visit_ExceptionNode(self, node):
        with self.BLOCK("exception", name = node.attrs["name"]):
            if node.attrs["extends"]:
                self.ATTR(extends = ",".join(base.attrs["name"] for base in node.attrs["extends"]))
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)
    
    def visit_RecordAttrNode(self, node):
        with self.BLOCK("attr", name = node.attrs["name"], type = node.attrs["type"]):
            self.emit_doc(node)

    def visit_ConstNode(self, node):
        with self.BLOCK("const", name = node.attrs["name"], type = node.attrs["type"]):
            if node.parent.modinfo.attrs["namespace"]:
                self.ATTR(namespace = node.parent.modinfo.attrs["namespace"])
            self.ATTR(value = node.attrs["value"]) 
            self.emit_doc(node)

    def visit_EnumNode(self, node):
        with self.BLOCK("enum", name = node.attrs["name"]):
            self.emit_doc(node)
            for child in node.children:
                child.accept(self)
    
    def visit_EnumAttrNode(self, node):
        with self.BLOCK("member", name = node.attrs["name"]):
            if "value" in node.attrs and node.attrs["value"] is not None:
                self.ATTR(value = node.attrs["value"])
            self.emit_doc(node)


class ServerGenerator(object):
    def __init__(self):
        self.doc = python.Module()
        self.BLOCK = self.doc.block
        self.STMT = self.doc.stmt
        self.SEP = self.doc.sep
        self.DOC = self.doc.doc
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
            self.STMT("agnos.servers.server_main({0}_bindings.ProcessorFactory(Handler(), exception_map))", 
                node.service_name)
        self.SEP()
    
    def visit_FuncNode(self, node):
        args = ", ".join(arg.attrs["name"] for arg in node.children)
        if node.parent.modinfo.attrs["namespace"]:
            namespace = node.parent.modinfo.attrs["namespace"]
            name = namespace.replace(".", "_") + "_" + node.attrs["name"]
        else:
            name = node.attrs["name"]
        if node.attrs["version"] and not node.latest:
            name += "_v%s" % (node.attrs["version"],)
        
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
        if node.parent.parent.modinfo.attrs["namespace"]:
            namespace = node.parent.parent.modinfo.attrs["namespace"].replace(".", "_") + "_"
        else:
            namespace = ""
        args = ", ".join(arg.attrs["name"] for arg in node.children)
        with self.BLOCK("def {0}_{1}(_self, {2})", namespace + node.parent.attrs["name"], node.attrs["name"], args):
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


def main(rootdir, outdir = None, idlfile = None, serverfile = None, rootpackage = None, history_file = None):
    filenames, rootdir = get_filenames(rootdir)
    if not rootpackage:
        rootpackage = os.path.basename(rootdir)
    try:
        ast_root = parse_source_files(rootdir, filenames, rootpackage)
    except SourceError as ex:
        ex.display()
        raise

    if not outdir:
        outdir = rootdir
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    if not idlfile:
        idlfile = os.path.join(outdir, "%s_autogen.xml" % (ast_root.service_name,))
    if not serverfile:
        serverfile = os.path.join(outdir, "%s_autogen_server.py" % (ast_root.service_name,))
    if not history_file:
        history_file = idlfile[:-4] + "_history"
    
    visitor = IdlGenerator(history_file)
    visitor.visit(ast_root)
    with open(idlfile, "w") as f:
        f.write(visitor.doc.render())

    compile(idlfile, PythonTarget(outdir))
    
    visitor = ServerGenerator()
    visitor.visit(ast_root)
    with open(serverfile, "w") as f:
        f.write(visitor.doc.render())
    




