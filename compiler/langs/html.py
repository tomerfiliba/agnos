from contextlib import contextmanager



class HtmlText(object):
    MAPPINGS = {
        "&" : "&amp;",
        "'" : "&apos;",
        '"' : "&quot;",
        "<" : "&lt;",
        ">" : "&gt;",
    }
    def __init__(self, text, *args):
        text = str(text)
        if args:
            text = text.format(*args)
        self.text = text
    @classmethod
    def escape(cls, text):
        return "".join(cls.MAPPINGS.get(ch, ch) for ch in text)
    def render(self):
        return [self.escape(self.text)]

class HtmlBlock(object):
    def __init__(self, _tag, **attrs):
        self.tag = _tag.lower()
        self.attrs = {}
        self.children = []
        self.stack = []
        for k, v in attrs.iteritems():
            self.attr(k, v)
    
    def _get_head(self):
        return self.stack[-1] if self.stack else self

    def attr(self, name, value):
        self._get_head().attrs[name.lower()] = str(value)
    def delattr(self, name):
        del self._get_head().attrs[name.lower()]
    def text(self, text, *args):
        self._get_head().children.append(HtmlText(text, *args))

    @contextmanager
    def block(self, *args, **kwargs):
        blk = HtmlBlock(*args, **kwargs)
        self._get_head().children.append(blk)
        self.stack.append(blk)
        yield blk
        self.stack.pop(-1)
    
    def render(self):
        attrs = " ".join('%s="%s"' % (k, HtmlText.escape(v)) 
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


class HtmlDoc(HtmlBlock):
    DOCTYPE = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')

    def __init__(self):
        HtmlBlock.__init__(self, "html", xmlns = "http://www.w3.org/1999/xhtml")
    def render(self):
        return self.DOCTYPE + "\n" + "\n".join(HtmlBlock.render(self))


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
            ATTR("border", 2)
            with BLOCK("tr"):
                with BLOCK("td"):
                    TEXT("hi there")
    
    print doc.render()





