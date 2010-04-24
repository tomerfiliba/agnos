import syntree


def toxml(node, level):
    ind = "\t" * level
    ind2 = "\t" * (level + 1)
    attrs = " ".join('%s="%s"' % (k, v) for k, v in sorted(node.attrs.items()))
    if node.children or node.doc:
        lines = ["%s<%s %s>" % (ind, node.TAG, attrs)]
        if node.doc:
            lines.append(ind2 + "<doc>")
            for l in node.doc:
                lines.append(ind2 + l)
            lines.append(ind2 + "</doc>")
        for child in node.children:
            lines.append(toxml(child, level + 1))
        lines.append("%s</%s>" % (ind, node.TAG,))
    else:
        lines = ["%s<%s %s/>" % (ind, node.TAG, attrs)]
    return "\n".join(lines)


def main(filename):
    ast_root = syntree.parse_source_file(filename)
    print toxml(ast_root, 0)
    #ast_root.display()



if __name__ == "__main__":
    try:
        main("examples/simple.py")
    except syntree.SourceError, ex:
        ex.display()


