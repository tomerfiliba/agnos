from compiler import compile, JavaTarget


if __name__ == "__main__":
    try:
        compile("tests/test.xml", JavaTarget("tests/gen-java"))
    except:
        import sys
        import pdb
        import traceback
        traceback.print_exception(*sys.exc_info())
        pdb.post_mortem(sys.exc_info()[2])



