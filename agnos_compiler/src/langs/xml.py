##############################################################################
# Part of the Agnos RPC Framework
#    http://agnos.sourceforge.net
#
# Copyright 2010, Tomer Filiba (tomerf@il.ibm.com; tomerfiliba@gmail.com)
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

class XmlComment(object):
    def __init__(self, text, *args):
        text = str(text)
        if args:
            text = text.format(*args)
        self.text = text
    def render(self):
        return ["<!-- %s -->" % (xml_escape(self.text),)]

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
    def comment(self, *args, **kwargs):
        self._get_head().children.append(XmlComment(*args, **kwargs))
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
                lines.extend(("\t" + l) for l in child.render())
            lines.append("</%s>" % (self.tag,))
        else:
            lines = ["<%s%s />" % (self.tag, attrs)]
        return lines


class XmlDoc(XmlBlock):
    ENCODING = '<?xml version="1.0" encoding="UTF-8"?>'

    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        pass
    def render(self):
        text = self.ENCODING + "\n" + "\n".join(XmlBlock.render(self))
        return text.encode("utf-8") 


class HtmlDoc(XmlBlock):
    DOCTYPE = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')

    def __init__(self):
        XmlBlock.__init__(self, "html", xmlns = "http://www.w3.org/1999/xhtml")
    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        pass
    def render(self):
        return self.DOCTYPE + "\n" + "\n".join(XmlBlock.render(self))



if __name__ == "__main__":
    with HtmlDoc() as doc:
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
    print "---------"
    
    with XmlDoc("service", name="moshe") as doc:
        with doc.block("doc"):
            doc.text("this is function opens the given file")
        with doc.block("arg", name="filename", type="str"):
            with doc.block("doc"):
                doc.text("this is the filename to open")
        doc.elem("this", elem="has no children")
    
    print doc.render()
    





