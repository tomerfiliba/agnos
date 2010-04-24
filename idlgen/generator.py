import syntree


def main(filename):
    ast_root = syntree.parse_source_file(filename)
    ast_root.display()



if __name__ == "__main__":
    try:
        main("examples/simple.py")
    except syntree.SourceError, ex:
        ex.display()


