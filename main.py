from compiler import compile, JavaTarget


if __name__ == "__main__":
    compile("tests/test.xml", JavaTarget("tests/gen-java"))



