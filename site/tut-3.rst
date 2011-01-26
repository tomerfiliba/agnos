Part 3: ``srcgen``
==================
:doc:`srcgen` is a powerful front-end to the Agnos compiler, which generates
the :doc:`idl` specification from special comments embedded in the source code.
Instead of having to write a lengthy XML file and keeping it up-to-date with
your service implementation, you can use ``srcgen``.

.. note::

   * At the moment, ``srcgen`` supports only ``python``.
   * Be sure to read the :doc:`reference <srcgen>`.

``srcgen`` works by scanning a directory (source code package) for ``.py`` 
files, and looks for special comments in the format of 
``#:: @tag [NAME] key1=val1 key2=val2 ...``, placed above the code. It relies
on **indentation** to express nesting, so keep in mind that whitespace matters.

You would want to use ``srcgen`` when you have a rather large project 
(typically a library) and only a single implementation for the service. 
Instead of starting by designing the service and writing (possibly large) IDL
file, ``srcgen`` allows you to start by writing the service and extending as 
you go. Let's start with an example.

RemoteFiles Reloaded
--------------------
Consider the following code:

.. code-block:: python

    #:: @service RemoteFiles
    
    #:: @enum
    class FileMode(object):
        #:: @member
        Read = 0
        #:: @member
        Write = 1
    
    #:: @exception
    class InvalidOperationForMode(Exception):
        #:: @attr filename type=str
        #:: @attr mode type=FileMode
        #:: @attr message type=str
        
        def __init__(self, filename, mode, msg):
            self.filename = filename
            self.mode = mode
            self.message = msg
    
    #:: @class
    class File(object):
        #:: @attr filename type=str access=get
        #:: @attr mode type=FileMode access=get
        #:: @attr closed type=str access=get
        
        def __init__(self, filename, mode):
            self.filename = filename
            self.mode = mode
            if mode == FileMode.Read:
                self.file = open(filename, "r")
            elif mode == FileMode.Write:
                self.file = open(filename, "w")
        
        @property
        def closed(self):
            return self.file == None
        
        #:: @method type=void
        #::     closes the file. after this, no IO can be performed.
        def close(self):
            if self.file is None:
                return
            self.file.close()
            self.file = None
        
        #:: @method type=buffer
        #::     reads up to `count` bytes from the file
        #::     note: the file must be opened for reading
        #::
        #::     @arg count type=int
        #::         the maximal number of bytes to read. `-1` means read 
        #::         until EOF
        def read(self, count):
            if self.mode != FileMode.Read:
                raise InvalidOperationForMode(self.filename, self.mode, "mode must be 'Read'")
            return self.file.read(count)

        #:: @method type=void
        #::     writes a chunk of data to the file
        #::     note: the file must be opened for writing
        #::
        #::     @arg data type=buffer
        #::         the data to write
        def write(self, data):
            if self.mode != FileMode.Write:
                raise InvalidOperationForMode(self.filename, self.mode, "mode must be 'Write'")
            return self.file.write(count)
    
    #:: @func type=File
    #::     returns a new File instance, representing the given file
    #::
    #::     @arg filename type=str
    #::     @arg mode type=FileMode 
    def openFile(filename, mode):
        return File(filename, mode)

Save it somewhere in a directory of its own, under the name RemoteFiles.py,
and then run::

   $ agnosrc-py /path/to/directory --packagename=.

.. note::

   * You should name the **directory** of the file, not the file itself
   * You can explore all of the command-line options :ref:`here <tool-agnosrc-py>`.
   * ``--packagename=.`` means the generated ``import`` statements will be 
     made relative to the same directory.

In your current directory, the following files should appear::

    RemoteFiles_autogen_history
    RemoteFiles_autogen_server.py
    RemoteFiles_autogen.xml
    RemoteFiles_bindings.py

Let's have a look at ``RemoteFiles_autogen.xml`` ::

    <?xml version="1.0" encoding="UTF-8"?>
    <service name="RemoteFiles">
        <enum name="FileMode">
            <member name="Read" value="0" />
            <member name="Write" value="1" />
        </enum>
        <exception name="InvalidOperationForMode">
            <attr name="filename" type="str" />
            <attr name="mode" type="FileMode" />
            <attr name="message" type="str" />
        </exception>
        <class name="File">
            <attr get="yes" getid="800000" name="filename" set="no" type="str" />
            <attr get="yes" getid="800001" name="mode" set="no" type="FileMode" />
            <attr get="yes" getid="800002" name="closed" set="no" type="bool" />
            <method id="800003" name="close" type="void">
                <doc>
                    closes the file. after this, no IO can be performed.
                </doc>
            </method>
            <method id="800004" name="read" type="buffer">
                <doc>
                    reads up to `count` bytes from the file
                    note: the file must be opened for reading
                </doc>
                <arg name="count" type="int">
                    <doc>
                        the maximal number of bytes to read. `-1` means read 
                        until EOF
                    </doc>
                </arg>
            </method>
            <method id="800005" name="write" type="void">
                <doc>
                    writes a chunk of data to the file
                    note: the file must be opened for writing
                </doc>
                <arg name="data" type="buffer">
                    <doc>
                        the data to write
                    </doc>
                </arg>
            </method>
        </class>
        <func id="800006" name="openFile" type="File">
            <doc>
                returns a new File instance, representing the given file
            </doc>
            <arg name="filename" type="str" />
            <arg name="mode" type="FileMode" />
        </func>
    </service>

You can see how similar it is to :ref:`our hand-written IDL <tut2-idl>`. It 
includes more comments and some ``id`` numbers (which we'll discuss in a 
minute), but otherwise identical to our previous version.


Using our Server
----------------
For the sake of simplicity, we'll work with a ``python`` client. You can, 
of course, use the auto-generated IDL to generate bindings for other languages
as well.

First, run the auto-generated server ::

  $ python RemoteFiles_autogen_server.py -p 12345
  
Now let's open an interactive ``python`` interpreter

.. code-block:: python

    >>> import RemoteFiles_bindings
    >>> c = RemoteFiles_bindings.Client.connect("localhost", 12345)
    >>> f = c.openFile("/tmp/ag2/RemoteFiles_autogen.xml", RemoteFiles_bindings.FileMode.Read)
    >>> f.read(20)
    '<?xml version="1.0" '
    >>> f.read(20)
    'encoding="UTF-8"?>\n<'
    >>> f.read(20)
    'service name="Remote'
    >>> f.closed
    False
    >>> f.filename
    u'/tmp/ag2/RemoteFiles_autogen.xml'
    >>> f.mode
    FileMode('Read' = 0)
    >>> f.write("foo")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "RemoteFiles_bindings.py", line 93, in write
        return self._client._funcs.sync_900027(self, data)
      File "RemoteFiles_bindings.py", line 390, in sync_900027
        return _self.utils.get_reply(seq)
      File "/usr/local/lib/python2.6/dist-packages/agnos/protocol.py", line 465, in get_reply
        raise obj
    RemoteFiles_bindings.InvalidOperationForMode: 
        InvalidOperationForMode(u'/tmp/ag2/RemoteFiles_autogen.xml', FileMode('Read' = 0), 
        u"mode must be 'Write'")
    >>> f.read(20)
    'Files">\n\t<enum name='
    >>> f.close()
    >>> f.closed
    True


The *History File* and ID Numbers
---------------------------------
As you can see, almost every element of the IDL includes an ``id`` attribute.
This ID is used to identify functions, methods, and class attributes, when 
they are invoked or referenced, so it is crucial that the two sides use the
same IDs. As long as both the client bindings and server bindings are 
generated from the same version of the IDL, they would use the same IDs and
everything would be fine. However, keeping all clients in sync with the server
is not always feasible, and in order to solve that, ``srcgen`` supports 
versioning. We'll not go into all the details here.

The *history file* lists fully-qualified function names and their respective 
IDs, so future invocations of ``srcgen`` will retain the old IDs. This allows
newer servers to be compatible with older clients. Therefore, the contents of
the history file are valuable, and it should be included in your source code
repository.





