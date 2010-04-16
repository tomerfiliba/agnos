class HtmlElem(object):
    TAG = None
    def __init__(self, *children, **attrs):
        self.children = list(children)
        self.attrs = attrs
    def __getattr__(self, name):
        return self.attrs[name]
    def __delattr__(self, name):
        del self.attrs[name]
    def __setattr__(self, name, value):
        self.attrs[name] = value
    def append(self, child):
        self.children.append(child)
    @classmethod
    def escape(cls, text):
        text = str(text)
        return text.replace('&', "&amp;").replace('"', "&quot;").replace("'", "&apos;")
    def render(self):
        attrs = " ".join('%s="%s"' % (self.escape(k), self.escape(v)) for k, v in sorted(self.attrs.items()))
        if self.children:
            return "<%s %s/>" % (self.TAG, attrs)
        else:
            children = "\n".join(child.render() for child in children)
            return "<%s %s>\n%s\n</%s>" % (self.TAG, attrs, children, self.TAG)

class Root(HtmlElem):
    TAG = "xhtml"
class Head(HtmlElem):
    TAG = "head"
class Body(HtmlElem):
    TAG = "body"
class Table(HtmlElem):
    TAG = "table"
class Row(HtmlElem):
    TAG = "tr"
class Cell(HtmlElem):
    TAG = "td"
class Para(HtmlElem):
    TAG = "p"

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












