from targets import JavaTarget
from compiler import compile


if __name__ == "__main__":
    compile("../tests/test.xml", JavaTarget("../tests/gen-java"))



