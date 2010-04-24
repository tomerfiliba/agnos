#:: @class
class File(object):
    #:: @ctor
    #::    @arg filename type=string
    #::    @arg mode type=string
    def __init__(self, filename, mode):
        self.file = open(filename, mode)

    #:: @attr filename type=str access=get
    @property
    def filename(self):
        return self.file.name

    #:: @method type=buffer
    #::    reads up to 'count' bytes from the file
    #::    @arg count type=int32
    #::        the number of bytes to read
    def read(self, count):
        return self.file.read(count)

    #:: @method type=str
    #::    writes the given buffer to the file
    #::    @arg data type=buffer
    def write(self, buffer):
        self.file.write(buffer)

    #:: @method
    def close(self):
        self.file.close()

    #:: @method type=void
    def flush(self):
        self.file.close()

#:: @func type=File
#::    opens the given file in the given mode and returns a File instance
#::    @arg filename type=str
#::        the name of the file to open
#::    @arg mode type=str
#::        the opening mode, either 'r' or 'w'
def open(filename, mode):
    return File(filename, mode)

#:: @func
#::    opens the given file in the given mode and returns a File instance
#::    @arg src type=File
#::        the name of the file to open
#::    @arg dst type=File
#::        the opening mode, either 'r' or 'w'
def copy(src, dst):
    while True:
        buf = src.read(10000)
        if not buf:
            break
        dst.write(buf)










