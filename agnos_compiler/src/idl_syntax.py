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
"""
a utility module for parsing consts and templated types (context-free grammar)
"""

WHITESPACE = " \t\n\r"

class IDLError(Exception):
    pass


def parse_const(text):
    stream = list(text)
    res = _parse_const(stream)
    trailing = "".join(stream).strip()
    if trailing:
        raise IDLError("trailing data after template: %r" % (trailing,))
    return res

def _parse_const(stream):
    while True:
        ch = stream[0]
        if ch in WHITESPACE:
            stream.pop(0)
        else:
            break
    if ch == "[":
        return _parse_list(stream)
    if ch == "{":
        return _parse_dict(stream)
    if ch in "0123456789":
        return _parse_number(stream)
    if ch in ("'", '"'):
        return _parse_string(stream)
    else:
        raise IDLError("invalid literal %r" % (ch,))

def _parse_list(stream):
    items = []
    assert stream.pop(0) == "["
    while True:
        if not stream:
            raise IDLError("list: missing closing ']'")
        ch = stream[0]
        if ch in WHITESPACE + ",": 
            stream.pop(0)
            continue
        if ch == "]":
            stream.pop(0)
            break
        else:
            items.append(_parse_const(stream))
    return items

def _parse_dict(stream):
    items = {}
    assert stream.pop(0) == "{"
    while True:
        if not stream:
            raise IDLError("dict: missing closing '}'")
        ch = stream[0]
        if ch in WHITESPACE + ",": 
            stream.pop(0)
            continue
        elif ch == "}":
            stream.pop(0)
            break
        else:
            k = _parse_const(stream)
            while True:
                ch = stream[0]
                if ch in WHITESPACE: 
                    stream.pop(0)
                    continue
                elif ch == ":":
                    stream.pop(0)
                    break
                else:
                    raise IDLError("dict item expected ':', found %r", ch)
            v = _parse_const(stream)
            items[k] = v
    return items

def _parse_number(stream):
    if stream[0:2] == ["0", "x"]:
        del stream[0:2]
        DIGSET = "0123456789abcdefABCDEF"
        base = 16
    elif stream[0:2] == ["0", "o"]:
        del stream[0:2]
        base = 8
        DIGSET = "01234567"
    elif stream[0:2] == ["0", "b"]:
        del stream[0:2]
        base = 2
        DIGSET = "01"
    else:
        base = 10
        DIGSET = "0123456789.eE+-"
    
    digits = []
    while stream:
        ch = stream[0]
        if ch in DIGSET:
            stream.pop(0)
            digits.append(ch)
        else:
            break
    digits = "".join(digits).lower()
    
    if "." in digits or "e" in digits:
        return float(digits)
    else:
        return int(digits, base)

STRING_ESCAPES = {
    "n" : "\n",
    "r" : "\r",
    "t" : "\t",
    "\\" : "\\",
    "'" : "'",
    '"' : '"',
}

def _parse_string(stream):
    delim = stream.pop(0)
    assert delim in ("'", '"')
    chars = []
    while True:
        if not stream:
            raise IDLError("string: missing closing quote")
        ch = stream.pop(0)
        if ch == delim:
            break
        elif ch == "\\":
            ch = stream.pop(0)
            if ch in STRING_ESCAPES:
                ch = STRING_ESCAPES[ch]
            elif ch == "x":
                d1 = stream.pop(0)
                d2 = stream.pop(0)
                ch = chr(int(d1,16)*16 + int(d2,16))
            ch = STRING_ESCAPES.get(ch, ch)
        chars.append(ch)
    return "".join(chars)


def parse_template(text):
    stream = list(text)
    res = _parse_template(stream)
    trailing = "".join(stream).strip()
    if trailing:
        raise IDLError("trailing data after template: %r" % (trailing,))
    return res

def _parse_template(stream):
    head = []
    children = []
    end_of_head = False
    while stream:
        ch = stream[0]
        if ch in WHITESPACE:
            stream.pop(0)
            end_of_head = True
            continue
        elif ch == "[":
            stream.pop(0)
            end_of_head = True
            child = None
            while True:
                ch = stream[0]
                if ch == "]":
                    stream.pop(0)
                    if child:
                        children.append(child)
                        child = None
                    break
                elif ch == ",":
                    stream.pop(0)
                    if child:
                        children.append(child)
                        child = None
                    else:
                        raise IDLError("expected identifier before ','")
                else:
                    child = _parse_template(stream)
        elif ch in ",]":
            break
        if end_of_head:
            break
        else:
            head.append(ch)
            stream.pop(0)
    return "".join(head), children


#if __name__ == "__main__":
#    try:
#        print parse_const(r"""[0x12, 11, 0b1110, 3.1415926535, 3.14e+19, 3.14e-19]""")
#        print parse_const(r"""['hello', "world", 'hi\n\r\tthere', 'hi\\there', 'hi\"there', 'hi\'there', 'hi\x20there']""")
#        print parse_const(r"""{1 : 2, "hello" : 17.3}""")
#        print parse_const(r"""[17, 18, 19] 20""")
#        print parse_const(r"""{17 : 18, 19 : 20} 21""")
#        print parse_template("map[int, list[str]]")
#    except IDLError:
#        raise
#    except Exception:
#        import pdb
#        import sys
#        import traceback
#        print "".join(traceback.format_exception(*sys.exc_info()))
#        pdb.post_mortem(sys.exc_info()[2])
    


















