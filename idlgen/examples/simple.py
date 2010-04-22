#:: struct
class StatRes(object):
    pass
    #:: attr inode: int32
    #:: attr mode: int32
    #:: attr atime: date
    #:: attr mtime: date
    #:: attr ctime: date


#:: class
class File(object):
    #:: ctor 
    #::    filename: string
    #::    mode: string
    def __init__(self, filename, mode):
        self.file = open(filename, mode)

    #:: attr filename
    @property
    def filename(self):
        return self.file.name

    #:: method: buffer
    #::    count: int32
    def read(self, count):
        return self.file.read(count)

    #:: method
    #::    data: buffer
    def write(self, buffer):
        self.file.write(buffer)

    #:: method
    def close(self):
        self.file.close()

    #:: method: void
    def flush(self):
        self.file.close()

#:: func: File
#::    opens the given file in the given mode and returns a File instance
#::    * filename: str
#::        the name of the file to open
#::    * mode: str
#::        the opening mode, either 'r' or 'w'
def open(filename, mode):
    return File(filename, mode)

#:: func: File
#::    opens the given file in the given mode and returns a File instance
#::    * filename: str
#::        the name of the file to open
#::    * mode: str
#::        the opening mode, either 'r' or 'w'
def copy(filename, mode):
    return File(filename, mode)










