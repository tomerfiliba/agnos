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

and generate the ``jar`` as explained :ref:`before <tut1-jar>`. Have a look at
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

As you can see, most of the boilerplate code has already been written for you,
but we still have some parts to fill in and do some tweaking:

.. code-block:: java

    // some imports ...
    import RemoteFiles.server_bindings.RemoteFiles;
    
    public class RemoteFilesServer {
        // classes
        public static class MyFile implements RemoteFiles.IFile {
            protected String _filename;
            protected RemoteFiles.FileMode _mode;
            protected FileInputStream fis;
            protected FileOutputStream fos;
    
            public MyFile(String filename, RemoteFiles.FileMode mode)
                    throws IOException {
                _filename = filename;
                _mode = mode;
                if (mode == RemoteFiles.FileMode.Read) {
                    fis = new FileInputStream(filename);
                } else if (mode == RemoteFiles.FileMode.Write) {
                    fos = new FileOutputStream(filename);
                }
            }
    
            // ...

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
                if (fis == null) {
                    throw new InvalidOperationForMode(_filename, _mode, "mode must be 'Read'");
                }
                byte[] data = new byte[count];
                fis.read(data, 0, count);
                return data;
            }
    
            public void write(byte[] data) throws Exception {
                if (fos == null) {
                    throw new InvalidOperationForMode(_filename, _mode, "mode must be 'Write'");
                }
                fos.write(data, 0, data.length);
            }
    
        }
    
        // handler
        public static class Handler implements RemoteFiles.IHandler {
            public RemoteFiles.IFile open(String filename, RemoteFiles.FileMode mode)
                    throws Exception {
                return new MyFile(filename, mode);
            }
    
        }
    
        // main ...
    }



.. code-block:: python

    >>> import RemoteFiles_bindings
    >>> c=RemoteFiles_bindings.Client.connect("localhost", 12345)
    >>> f=c.open("/tmp/agnos-test/myidl.xml", RemoteFiles_bindings.FileMode.Read)
    >>> f
    <FileProxy instance @ 1>
    
    >>> f.filename
    u'/tmp/agnos-test/myidl.xml'
    >>> f.mode
    FileMode('Read' = 0)
    >>> f.closed
    False

    >>> f.read(200)
    '<service name="RemoteFiles">\n    <enum name="FileMode">\n        <member n
    ame="Read" />\n        <member name="Write" />\n        <member name="ReadWr
    ite" />\n    </enum>\n    \n    <class name="File">\n    '
    
    >>> f.read(200)
    '    <attr name="filename" type="str" set="no"/>\n        <attr name="mode" 
    type="FileMode" set="no"/>\n        <attr name="closed" type="bool" set="no"
    />\n\n        <method name="close" type="void" />\n   '
    
    >>> f.close()
    >>> f.closed
    True
    
    >>> f.read(200)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "RemoteFiles_bindings.py", line 61, in read
        return self._client._funcs.sync_900030(self, count)
      File "RemoteFiles_bindings.py", line 357, in sync_900030
        return _self.utils.get_reply(seq)
      File "/usr/local/lib/python2.6/dist-packages/agnos/protocol.py", line 465, in get_reply
        raise obj
    agnos.protocol.GenericException: java.lang.NullPointerException
    ---------------- Remote Traceback ----------------
            at RemoteFilesServer$MyFile.read(RemoteFilesServer.java:54)
            at RemoteFiles.server_bindings.RemoteFiles$Processor.processInvoke(RemoteFiles.java:350)
            at agnos.protocol.BaseProcessor.process(BaseProcessor.java:147)
            at agnos.servers.BaseServer._serveClient(BaseServer.java:60)
            at agnos.servers.SimpleServer.serveClient(SimpleServer.java:39)
            at agnos.servers.BaseServer.serve(BaseServer.java:50)
            at agnos.servers.CmdlineServer.main(CmdlineServer.java:124)
            at RemoteFilesServer.main(RemoteFilesServer.java:82)
    
    >>>



























