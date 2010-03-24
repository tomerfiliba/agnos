from .base import TargetBase
from . import blocklang
from contextlib import contextmanager


class JavaTarget(TargetBase):
    @contextmanager
    def new_module(self, filename):
        mod = blocklang.Module()
        yield mod
        with self.open(filename) as f:
            f.write(mod.render())

    def generate(self, service):
        self.generate_records(service)
    
    def generate_records(self, service):
        with self.new_module(service.name) as module:
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            
            #STMT("package {0}", service.name)
            #SEP()
            STMT("import agnos.*")
            STMT("import java.util.*")
            SEP()
            
            with BLOCK("public class Records"):
                for rec in service.types:
                    if isinstance(rec, compiler.Record):
                        self.generate_record(module, rec)
    
    def generate_record(self, module, rec):
        BLOCK = module.block
        STMT = module.stmt
        SEP = module.sep
        with BLOCK("public static class {0}", rec.name):
            for mem in rec.members:
                STMT("public {0} {1}", type_to_java(mem.type), mem.name)
            SEP()
            with BLOCK("public {0}()", rec.name):
                pass
            args = ", ".join("%s %s" % (type_to_java(mem.type), mem.name) for mem in rec.members)
            with BLOCK("public {0}({1})", rec.name, args):
                for mem in rec.members:
                    STMT("this.{0} = {0}", mem.name)
        
        with BLOCK("public static class _{0}Record implements IDatatype", rec.name):
            with BLOCK("public void pack(Object obj, OutputStream stream) throws IOException"):
                STMT("{0} val = ({0})obj", rec.name)
                for mem in rec.members:
                    STMT("{0}.pack(val.{1}, stream)", type_to_packer(mem.type), mem.name)

            with BLOCK("public Object unpack(InputStream stream) throws IOException"):
                args = ", ".join("(%s)%s.unpack(stream)" % (type_to_java(mem.type), type_to_packer(mem.type)) for mem in rec.members)
                STMT("return new {0}({1})", rec.name, args)
        
        STMT("protected static _{0}Record {0}Record = new _{0}Record()", rec.name)































