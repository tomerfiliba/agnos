Part 2: By-Value and By-Reference
=================================

The :doc:`first part <tut-1>` of the tutorial has introduced you to the 
:ref:`Agnos Compiler <tool-agnosc>`, how to implement a basic server,
and how to write a simple client. We have not delved too deeply into the
syntax and semantics of the IDL and its the different elements, since assumed 
it's self-explanatory enough (of course you can refer to the 
:doc:`reference documentation <idl>` for more info). 

In this part we'll learn more about three important constructs: **records**, 
**classes**, and **exceptions**, and the difference between passing objects
:ref:`By-Value and By-Reference <concepts-by-val-by-ref>`. 

.. note::
   As with the first part, this tutorial is not an exhaustive reference either.

**Records** are basically a collection of attributes (each with a name and a 
type), and they **pass by value**, meaning, they are serialized to bytes and 
sent to the other side, where they are reconstructed. This essentially means 
you now have two **copies** of the object, and changes made to one of the 
copies will **not** propagate to the other. 

**Classes**, on the other, represent objects that have internal state 
(*attributes* or *properties*) and expose methods that alter that state.
In practice, not all objects can be copied -- many times it is not possible
or does not make sense. For instance, think of an open file handle, or a 
physical device driver (like a printer), or even simply or a very large data 
set (Google's database). 
If we stick with the open file handle example, internally it is represented as 
an integer -- but passing this integer to the other party is meaningless -- 
there's it can do with that number. So instead of copying the internal state of 
the object, we pass it **by reference**, meaning we only send a unique 
identifier of that object. 
On the other side (normally the client), a **proxy object** is created to 
represent the remote object (through the unique identifier). Every operation
that's performed on the proxy object is reflected on the remote object, which 
allows the proxy object to have the same "looks and feel" as the remote one.

.. note::
   Records are not limited to value types -- they can contain attributes of 
   class types too.

**Exceptions** are special objects that are used to represent "exceptional" or
erroneous situations. In Agnos, they are but a specialized form of records, 
which derive from the relevant exception base class in the target language. 
Being records, exceptions are passed **by value** too.

.. _tut2-idl:

Example
-------
Consider the following IDL:

.. code-block:: xml

    <service name="RemoteFiles">
        <enum name="FileMode">
            <member name="Read" />
            <member name="Write" />
        </enum>
        
        <exception name="InvalidOperationForMode">    
            <attr name="filename" type="str" />
            <attr name="mode" type="FileMode" />
            <attr name="message" type="str" />
        </exception>
        
        <class name="File">
            <attr name="filename" type="str" set="no"/>
            <attr name="mode" type="FileMode" set="no"/>
            <attr name="closed" type="bool" set="no"/>
    
            <method name="close" type="void" />
            
            <method name="read" type="buffer">
                <arg name="count" type="int"/>
            </method> 
    
            <method name="write" type="void">
                <arg name="data" type="buffer"/>
            </method> 
        </class>
        
        <func name="open" type="File">
            <arg name="filename" type="str" />
            <arg name="mode" type="FileMode" />
        </func>
    </service>

Run ::

  agnosc -t java -o src RemoteFiles.xml

and generate the ``jar`` as explained :ref:`previously <tut1-jar>`. Have a look at
the stub file that's generated for you:

.. code-block:: java

    // some imports...
    import RemoteFiles.server_bindings.RemoteFiles;
    
    public class ServerStub {
        // classes
        public static class File implements RemoteFiles.IFile {
            protected String _filename;
            protected RemoteFiles.FileMode _mode;
            protected Boolean _closed;
    
            public File(String filename, RemoteFiles.FileMode mode, Boolean closed) {
                _filename = filename;
                _mode = mode;
                _closed = closed;
            }
    
            public String get_filename() throws Exception {
                return _filename;
            }
    
            public RemoteFiles.FileMode get_mode() throws Exception {
                return _mode;
            }
    
            public Boolean get_closed() throws Exception {
                return _closed;
            }
    
            public void close() throws Exception {
                // implement me
            }
    
            public byte[] read(Integer count) throws Exception {
                // implement me
            }
    
            public void write(byte[] data) throws Exception {
                // implement me
            }
    
        }
    
        // handler
        public static class Handler implements RemoteFiles.IHandler {
            public RemoteFiles.IFile open(String filename, RemoteFiles.FileMode mode)
                    throws Exception {
                // implement me
            }
    
        }
        
        // main ...
    }

Server Code
-----------

As you can see, most of the boilerplate code has already been written for you,
but we still have some parts to fill in, and some tweaking to do. The code 
below is provided in whole:

.. code-block:: java

    import java.util.*;
    import java.io.*;
    import agnos.util.HeteroMap;
    import agnos.protocol.*;
    import agnos.servers.CmdlineServer;
    import RemoteFiles.server_bindings.RemoteFiles;
    
    public class RemoteFilesServer {
        //
        // classes
        //
        public static class MyFile implements RemoteFiles.IFile {
            protected String _filename;
            protected RemoteFiles.FileMode _mode;
            protected FileInputStream fis;
            protected FileOutputStream fos;
    
            public MyFile(String filename, RemoteFiles.FileMode mode) throws IOException {
                _filename = filename;
                _mode = mode;
                if (mode == RemoteFiles.FileMode.Read) {
                    fis = new FileInputStream(filename);
                }
                else if (mode == RemoteFiles.FileMode.Write) {
                    fos = new FileOutputStream(filename);
                }
            }
    
            public String get_filename() throws Exception {
                return _filename;
            }
    
            public RemoteFiles.FileMode get_mode() throws Exception {
                return _mode;
            }
    
            public Boolean get_closed() throws Exception {
                return fis == null && fos == null;
            }
    
            public void close() throws Exception {
                if (fis != null) {
                    fis.close();
                    fis = null;
                }
                if (fos != null) {
                    fos.close();
                    fos = null;
                }
            }
    
            public byte[] read(Integer count) throws Exception {
                if (get_closed()) {
                    throw new EOFException("file is closed");
                }
                if (_mode != RemoteFiles.FileMode.Read) {
                    throw new RemoteFiles.InvalidOperationForMode(_filename, 
                        _mode, "mode must be 'Read'");
                }
                byte[] data = new byte[count];
                fis.read(data, 0, count);
                return data;
            }
    
            public void write(byte[] data) throws Exception {
                if (get_closed()) {
                    throw new EOFException("file is closed");
                }
                if (_mode != RemoteFiles.FileMode.Write) {
                    throw new RemoteFiles.InvalidOperationForMode(_filename, 
                        _mode, "mode must be 'Write'");
                }
                fos.write(data, 0, data.length);
            }
        }
    
        //
        // handler
        //
        public static class Handler implements RemoteFiles.IHandler {
            public RemoteFiles.IFile open(String filename, RemoteFiles.FileMode mode)
                    throws Exception {
                return new MyFile(filename, mode);
            }
    
        }
    
        //
        // main
        //
        public static void main(String[] args) {
            CmdlineServer server = new CmdlineServer(
                    new RemoteFiles.ProcessorFactory(new Handler()));
            try {
                server.main(args);
            } catch (Exception ex) {
                ex.printStackTrace(System.err);
            }
        }
    
    }

The above code will compile (with the necessary jars), and you could run it
from the command line (don't forget to specify the port number, e.g., 
``-p 12345``).

Client Code
-----------
Generate the ``python`` bindings (i.e., ``agnosc -t python RemoteFiles.xml``),
and let's dive in:

.. code-block:: python

    >>> import RemoteFiles_bindings
    
    # create the client instance
    >>> c = RemoteFiles_bindings.Client.connect("localhost", 12345)
    
    # open some file for reading
    >>> f = c.open("/tmp/agnos-test/myidl.xml", RemoteFiles_bindings.FileMode.Read)
    
    # as you can see, we got back a file proxy object
    >>> f
    <FileProxy instance @ 1>
    
    # and it behaves as you might expect
    >>> f.closed
    False

    >>> f.read(20)
    '<service name="Remot'
    >>> f.read(20)
    'eFiles">\n    <enum n'
    >>> f.read(20)
    'ame="FileMode">\n    '
    
    # but since we opened it for reading, writing will fail
    >>> f.write("foo")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "RemoteFiles_bindings.py", line 93, in write
        return self._client._funcs.sync_900034(self, data)
      File "RemoteFiles_bindings.py", line 385, in sync_900034
        return _self.utils.get_reply(seq)
      File "/usr/local/lib/python2.6/dist-packages/agnos/protocol.py", line 465, in get_reply
        raise obj
    RemoteFiles_bindings.InvalidOperationForMode: 
       InvalidOperationForMode(u'/tmp/agnos-test/myidl.xml', FileMode('Read' = 0), 
       u"mode must be 'Write'")
    
    # don't worry, nothing's broke
    >>> f.read(10)
    '    <membe'
    >>> f.closed
    False
    
    # let's close the file
    >>> f.close()
    >>> f.closed
    True
    
    # so if we tried reading again, it won't work
    >>> f.read(20)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "RemoteFiles_bindings.py", line 91, in read
        return self._client._funcs.sync_900033(self, count)
      File "RemoteFiles_bindings.py", line 394, in sync_900033
        return _self.utils.get_reply(seq)
      File "/usr/local/lib/python2.6/dist-packages/agnos/protocol.py", line 465, in get_reply
        raise obj
    agnos.protocol.GenericException: java.io.EOFException: file is closed
    ---------------- Remote Traceback ----------------
        at RemoteFilesServer$MyFile.read(RemoteFilesServer.java:54)
        at RemoteFiles.server_bindings.RemoteFiles$Processor.processInvoke(RemoteFiles.java:402)
        at agnos.protocol.BaseProcessor.process(BaseProcessor.java:147)
        at agnos.servers.BaseServer._serveClient(BaseServer.java:60)
        at agnos.servers.SimpleServer.serveClient(SimpleServer.java:39)
        at agnos.servers.BaseServer.serve(BaseServer.java:50)
        at agnos.servers.CmdlineServer.main(CmdlineServer.java:124)
        at RemoteFilesServer.main(RemoteFilesServer.java:93)
    
    >>>

As you can see, the ``FileProxy`` instance looks and behaves just like the
real object, reflecting all local operations on the remote one.

You may also have noticed we got two kinds of exceptions, each with a different 
kind of traceback: the first is an exception of type 
``RemoteFiles_bindings.InvalidOperationForMode``, while the second is an 
exception of type ``agnos.protocol.GenericException``. The ``InvalidOperationForMode``
exception was defined by our IDL, may contain custom members, and is thrown
explicitly by our code (see the ``read`` and ``write`` methods of class 
``MyFile``).

The ``GenericException``, on the other hand, wraps an "external" exception 
(one that was not defined by the IDL). You can't throw a ``GenericException`` 
directly, but any exception that Agnos does not recognize will be wrapped by
one. As you can see, the ``GenericException`` includes the server's traceback
(which may not be pretty at all ;).



