WHITESPACE = " \t\n\r"
IDENTIFIER_FIRST = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
IDENTIFIER_REST = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"

def parse_const(stream):
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
        ch = stream[0]
        if ch in WHITESPACE + ",": 
            stream.pop(0)
            continue
        if ch == "]":
            stream.pop(0)
            break
        else:
            items.append(parse_const(stream))
    return items

def _parse_dict(stream):
    items = []
    assert stream.pop(0) == "{"
    while True:
        ch = stream[0]
        if ch in WHITESPACE + ",": 
            stream.pop(0)
            continue
        elif ch == "}":
            stream.pop(0)
            break
        else:
            k = parse_const(stream)
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
            v = parse_const(stream)
            items[k] = v
    return items

def _parse_number(stream):
    if stream[0:2] == ["0", "x"]:
        del stream[0:2]
        DIGSET = "0123456789abcdefABCDEF"
        base = 16
    
    elif stream[0:2] == ["0", "o"]:
        del stream[0:2]
        base = 10
        DIGSET = "01234567"
    elif stream[0:2] == ["0", "b"]:
        del stream[0:2]
        base = 10
        DIGSET = "01"
    else:
        base = 10
        DIGSET = "0123456789.eE+-"
    
    digits = []
    while True:
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
    "\\" : "\\",
    "'" : "'",
    '"' : '"',
}

def _parse_string(stream):
    delim = stream.pop(0)
    assert delim in ("'", '"')
    chars = []
    while True:
        ch = stream[0]
        if ch == delim:
            stream.pop(0)
            break
        elif ch == "\\":
            stream.pop(0)
            ch = stream.pop(0)
            if ch in STRING_ESCAPES:
                ch = STRING_ESCAPES[ch]
            elif ch == "x":
                d1=stream.pop(0)
                d2=stream.pop(0)
                ch = chr(int(d1,16)*16 + int(d2,16))
            ch = STRING_ESCAPES.get(ch, ch)
        chars.append(ch)
    return "".join(chars)



def parse_template(stream):
    head = []
    children = []
    while stream:
        ch = stream[0]
        if ch in WHITESPACE:
            stream.pop(0)
            continue
        elif ch == "[":
            stream.pop(0)
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
                    child = parse_template(stream)
        elif ch in ",]":
            break
        else:
            head.append(ch)
            stream.pop(0)
    return "".join(head), children

print parse_template(list("map[int,str]"))


















