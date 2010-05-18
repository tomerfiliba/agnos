from contextlib import contextmanager


MAPPINGS = {
    "&" : "&amp;",
    "'" : "&apos;",
    '"' : "&quot;",
    "<" : "&lt;",
    ">" : "&gt;",
}

def xml_escape(text):
    return "".join(MAPPINGS.get(ch, ch) for ch in text)

class XmlText(object):
    def __init__(self, text, *args, **kwargs):
        text = str(text)
        if args:
            text = text.format(*args)
        self.text = text
        self.escape = kwargs.pop("escape", True)
        if kwargs:
            raise TypeError("invalid keyword argument(s): %r" % (kwargs.keys(),))
    def render(self):
        if self.escape:
            return [xml_escape(self.text)]
        else:
            return [self.text]

class XmlBlock(object):
    def __init__(self, _tag, **attrs):
        self.tag = _tag.lower()
        self.attrs = {}
        self.children = []
        self.stack = []
        self.attr(**attrs)
    
    def _get_head(self):
        return self.stack[-1] if self.stack else self

    def attr(self, **kwargs):
        head = self._get_head()
        for k, v in kwargs.iteritems():
            head.attrs[k.lower()] = str(v)
    def delattr(self, name):
        del self._get_head().attrs[name.lower()]
    def text(self, *args, **kwargs):
        self._get_head().children.append(XmlText(*args, **kwargs))
    def elem(self, *args, **attrs):
        with self.block(*args, **attrs):
            pass

    @contextmanager
    def block(self, *args, **kwargs):
        blk = XmlBlock(*args, **kwargs)
        self._get_head().children.append(blk)
        self.stack.append(blk)
        yield blk
        self.stack.pop(-1)
    
    def render(self):
        attrs = " ".join('%s="%s"' % (k, xml_escape(v)) 
            for k, v in sorted(self.attrs.iteritems()))
        if attrs:
            attrs = " " + attrs
        if self.children:
            lines = ["<%s%s>" % (self.tag, attrs)]
            for child in self.children:
                lines.extend(("    " + l) for l in child.render())
            lines.append("</%s>" % (self.tag,))
        else:
            lines = ["<%s%s />" % (self.tag, attrs)]
        return lines


class XmlDoc(XmlBlock):
    ENCODING = '<?xml version="1.0" encoding="UTF-8"?>'

    def render(self):
        text = self.ENCODING + "\n" + "\n".join(XmlBlock.render(self))
        return text.encode("utf-8") 


class HtmlDoc(XmlBlock):
    DOCTYPE = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')

    def __init__(self):
        XmlBlock.__init__(self, "html", xmlns = "http://www.w3.org/1999/xhtml")
    def render(self):
        return self.DOCTYPE + "\n" + "\n".join(XmlBlock.render(self))


if __name__ == "__main__":
    doc = HtmlDoc()
    BLOCK = doc.block
    TEXT = doc.text
    ATTR = doc.attr
    
    with BLOCK("head"):
        with BLOCK("title"):
            TEXT("hello {0}", "world")
    with BLOCK("body"):
        with BLOCK("table", width = 15):
            ATTR(border = 2)
            with BLOCK("tr"):
                with BLOCK("td"):
                    TEXT("<b>hi</b> there", escape = False)
    
    print doc.render()
    
    doc = XmlDoc("service", name = "moshe")
    BLOCK = doc.block
    TEXT = doc.text
    ELEM = doc.elem

    with BLOCK("func", name = "open", type="File"):
        with BLOCK("doc"):
            TEXT("this is function opens the given file")
        with BLOCK("arg", name="filename", type="str"):
            with BLOCK("doc"):
                TEXT("this is the filename to open")
        ELEM("this", elem="has no children")
    
    print doc.render()
    





