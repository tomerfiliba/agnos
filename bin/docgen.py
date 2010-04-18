

def main(filename):
    service = compiler.load_spec(filename)
    doc = Root()
    body = Body()
    for mem in service.members:
        if isinstance(mem, compiler.Typedef):
            pass
        elif isinstance(mem, compiler.Const):
            pass
        elif isinstance(mem, compiler.Enum):
            pass
        elif isinstance(mem, compiler.Record):
            pass
        elif isinstance(mem, compiler.Exception):
            pass
        elif isinstance(mem, compiler.Class):
            pass
        else:
            assert False, "invalid member"












