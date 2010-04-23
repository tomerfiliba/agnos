class FileProcessor(object):
    def __init__(self, filename):
        self.file = open(filename, "r")
        self.lines = iter(self.file)
    
    def process(self):
        for line in self.lines:
            indentation = len(line) - len(line.lstrip())
            line = line.strip()
            if not line.startswith("#::"):
                continue
            print "!!", line
            line = line[3:]
            indentation += len(line) - len(line.lstrip())
            tokens = line.split()
            if tokens[0].endswith(":"):
                tokens[0] = tokens[0][:-1]
                tokens.insert(1, ":")
            if tokens[0] == "class":
                self.process_class(tokens)
            elif tokens[0] == "func":
                self.process_func(tokens)
            else:
                print "unknown keyword: ", tokens[0]
    
    def process_class(self, tokens):
        pass

    def process_func(self, tokens):
        pass


if __name__ == "__main__":
    p = FileProcessor("examples/simple.py")
    p.process()




