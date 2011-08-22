.. _doc-impl-targets:

Implementing Targets
====================
If you wish to implement new language-bindings support in Agnos, you first have you get 
acquainted with the internal workings of the tool-chain. From a bird's eye view, there are 
three parts that constitute an Agnos target: the code generator (compiler), the protocol 
implementation (``libagnos``), and the source-generator (``srcgen``)

.. note:: 
   Don't forget the :ref:`doc-restful`. It is very useful for small-scale projects,
   and is much simpler than having to implement a full-blown target language for Agnos.
   If you need to consume a simple Agnos service, and if your language has an easy-to-use 
   HTTP/REST library -- just stick with it.
   
   If you need to implement an Agnos service (server), the RESTful front-end won't 
   help you though, and you'll have to implement a target.


Compiler Target
===============
The first thing you'll want to do, when developing a new target for Agnos, is to implement
the compiler target. The itself compiler is written in python, so the natural (and recommended)
way to interface with- and extend it is in python. However, if you wish to re-implement all
of the compiler's logic (parsing, etc.) yourself in a different langauge, nobody's stopping
you :)

Under :file:`compiler/src/agnos_compiler/targets` are all of the currently-supported or planned
targets, one for each language. If your target gets too big, you may want to convert it to
a subpackage. The "reference implementation" you should follow is the Java one for 
"static languages" and the python one for "dynamic languages". 

Your target should derive from ``TargetBase`` -- this is not mandatory, but the base class 
provides some useful helper functions. The only interface method that you need to implement is
``generate()``, which is passed a ``service`` object that contains all the records, enums,
constants, classes and functions defined in the IDL. This method should take the ``service``
object and generate the appropriate code for the target language.

Language Generation Framework
-----------------------------
Agnos is using a sophisticated code generation framework that would (eventually) be released
as a separate project. It uses 
`context managers <http://docs.python.org/reference/compound_stmts.html#the-with-statement>`_
to correctly express the nesting levels of code blocks, in a fashion that's consistent
both with the generator and the generated code. These frameworks basically encapsulate the
notions of statements, (nested) blocks, and comments in the target language, so you don't
have to add semicolons or close braces manually every time. Note, however, that this framework is 
more syntactic than semantic -- it doesn't attempt to cover the various constructs (``if``, 
``for``, ``class``, ...) of the target language, only the basic layout of a module. The use of 
context managers enables the framework to "remember" the current nesting level automatically,
thus simplifying the code.

Here's an example of the ``c-like`` language framework::

    mod = Module()
    BLOCK = mod.block
    STMT = mod.stmt
    DOC = mod.doc
    SEP = mod.sep
    
    STMT("using System")
    STMT("using System.Collections")
    SEP(2)
    with BLOCK("namespace foo.bar"):
        DOC("this is a very special class")
        with BLOCK("public class Spam"):
            STMT("private int x, y")
            SEP()
            with BLOCK("public Spam()"):
                STMT("x = {0}", 17)
                STMT("y = {0}", 18)
            SEP()
            with BLOCK("public ~Spam()"):
                STMT("Dispose(false)")
    
    print mod.render()

Which yields

.. code-block:: c#

    using System;
    using System.Collections;
    
    
    namespace foo.bar
    {
        // this is a very special class
        public class Spam
        {
            private int x, y;
            
            public Spam()
            {
                x = 17;
                y = 18;
            }
            
            public ~Spam()
            {
                Dispose(false);
            }
        }
    }

As you can see, blocks are converted to properly-indented and braced entities, while statements
are semicolon-terminated. Nothing too fancy -- but notice how the structure of the generator 
is exactly the same as that of the generated code! It makes the generator much easier to read,
write and and debug. 

Agnos comes without language frameworks for python, C/C++, C-like languages (C#, Java) and XML.
You can always add your own (it's not at all complicated), but it's usually not necessary, since
the syntax of most languages is loosely based on C, which means the C-like would fit your needs.

Target Skeleton
---------------
Here's the general skeleton you should start with, when implementing a new target::

    from .base import TargetBase, NOOP
    from .. import compiler
    from ..compiler import is_complex_type
    
    class VBTarget(TargetBase):
        from ..langs import vblang
        LANGUAGE = vblang
    
        def generate(self, service):
            with self.new_module("%sBindings.vb" % (service.name,)) as module:
                BLOCK = module.block
                STMT = module.stmt
                SEP = module.sep
                
                STMT("Import System")
                STMT("Import Agnos")
                SEP()
                with BLOCK("Module {0}", service.name):
                    self._generate_types(module, service)
                    self._generate_server_bindings(module, service)
                    self._generate_client_bindings(module, service)

        def _generate_types(self, module, service):
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            
            for enum in service.enums():
                self._generate_enum(module, enum)
            
            for rec in service.records():
                self._generate_record(module, rec)
            
            for exc in service.records():
                self._generate_exception(module, exc)

            # packers for non-compelx types
            for rec in service.records_and_exceptions(lambda mem: not is_complex_type(mem)):
                self.generate_record_packer(module, rec)
                SEP()
            
            for cnst in service.consts.values():
                self._generate_const(module, cnst)
            
            for cls in service.classes():
                self._generate_class(module, cls)
    
        def _generate_server_bindings(self, module, service):
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            
            with BLOCK("Module Server"):
                pass # ...
    
        def _generate_client_bindings(self, module, service):
            BLOCK = module.block
            STMT = module.stmt
            SEP = module.sep
            
            with BLOCK("Module Client", service.name):
                pass # ...


Adding the Target
-----------------
And last but not least -- you'll want to add your target language to the ``agnosc`` command-line 
tool. This is done by editing :file:`compiler/bin/agnosc`, adding the necessary import for
your target, and adding the argument name to the ``TARGET_ALIASES`` dictionary.


.. ###############################################################################################


Library
=======
The next step is to implement ``libagnos`` for your target language. This library implements
the Agnos protocol, and usually consist of defining the necessary protocol constants,
packers (serializers), IO abstraction layer (transports) and various other helper functions.
You should place your code under the :file:`libagnos` directory, and provide the appropriate
packaging and/or build-system integration. Agnos uses `scons <http://www.scons.org/>`_,
as it's very powerful and extensible, but you're free to your a better build system if you
find it better. As explained before, you should follow the layout of the Java implementation
for static languages and the layout of the python implementation for dynamic ones. Quite a lot
of effort has been put into this design, and following it may save you considerable time, 
as well as shorten the learning-curve of end users, as they only have to learn one API.


Packers
-------
Packers are object "serializers": they have a ``pack()`` and ``unpack()`` methods,
that convert a "living" object into a sequence of bytes and vice versa. From a more
mathematical point of view, ``unpack`` and ``pack`` are inverse functions, such that
``unpack(pack(obj)) == obj`` and ``pack(unpack(buffer)) == buffer``.

In Java, we define an abstract class (could also be an interface) called ``AbstractPacker``,
which looks like so:

.. code-block:: java

    public abstract class AbstractPacker
    {
        abstract public void pack(Object obj, ITransport transport) throws IOException;
        abstract public Object unpack(ITransport transport) throws IOException;
        abstract public int getId();
    }

Then, all the built-in types have their packers, which simply extend ``AbstractPacker``.
For example, here's a sketch of the ``Int32Packer``:

.. code-block:: java

    public class Int32Packer extends AbstractPacker
    {
        @Override
        public void pack(Object obj, ITransport transport) throws IOException
        {
            int val = obj == null ? 0 : ((Number)obj).intValue();
            byte[] buffer = new byte[4];
            buffer[0] = (byte) ((val >> 24) & 0xff);
            buffer[1] = (byte) ((val >> 16) & 0xff);
            buffer[2] = (byte) ((val >> 8) & 0xff);
            buffer[3] = (byte) (val & 0xff);
            transport.write(buffer);
        }
    
        @Override
        public Object unpack(ITransport transport) throws IOException
        {
            byte[] buffer = new byte[4];
            transport.read(buffer);
            return new Integer(((int) (buffer[0] & 0xff) << 24) | ((int) (buffer[1] & 0xff) << 16)
                    | ((int) (buffer[2] & 0xff) << 8) | (int) (buffer[3] & 0xff));
        }
    }

Because of the limitations of programming languages like Java, we can't use the 
class directly, and so we create a singleton for each such packer, which is what
we'll use when we want to actually pack or unpack data.   

Packers can make use of one another, which greatly simplifies their implementation.
For example, when packing a ``Date`` object, you can convert it to a 64-bit that
represents the number of microseconds since January 1st, year 1, and then just call 
``Int64.pack(num_of_microseconds)``.

Packers can also be composed to form more complex packers. For example, the Agnos
compiler generates a packer for each :ref:`record <idl-record>` -- packing all of 
its fields, one after the other.

.. code-block:: java

    class Address
    {
        public State state;
        public String city;
        public String street;
        public Integer num;
        //...
    }

    class _AddressPacker extends AbstractPacker
    {
        public void pack(Object obj, ITransport transport) throws IOException
        {
            Address val = (Address)obj;
            StatePacker.pack(val.state, transport);
            Builtin.Str.pack(val.city, transport);
            Builtin.Str.pack(val.street, transport);
            Builtin.Int32.pack(val.num, transport);
        }
        public Object unpack(ITransport transport) throws IOException
        {
            return new Address(
                (State)StatePacker.unpack(transport),
                (String)Builtin.Str.unpack(transport),
                (String)Builtin.Str.unpack(transport),
                (Integer)Builtin.Int32.unpack(transport)
            );
        }
        //...
    }
    
    _AddressPacker AddressPacker = new _AddressPacker();
    //...
    Address myAddress = new Address(States.TX, "Dallas", "Main Rd.", 1234);
    AddressPacker.pack(myAddress);

Another important thing about packers is that each packer has a unique ID (unique
within in the same service definition). The packers for built-in types are
have ID in the range of 0-999, and the compiler-generated packers (like the 
``_AddressPacker`` above) get some random unique ID. 

These IDs are required for the ``HeteroMap`` type. Since it contains heterogeneous
keys and values, it has to associate a key-type and value-type to each key-value pair.
This is done by indicating the packer IDs of both key-type and value-type in
the wire-format.

But in this case, I belive, code speaks clearer than words. Refer to the  
`Java sources <http://github.com/tomerfiliba/agnos/tree/master/libagnos/java/src/agnos/packers>`_
for the complete picture.

.. note::
   Although the Java version is considered the *reference implementation*,
   don't go about converting it one-to-one to your target language.
   Java's type system is quite limited and enforced some arbitrary constraints.
   If you language has a different type system, you may have better alternatives -- 
   use the best practice for your language. For instance, *dynamic languages* would be 
   better off basing their code on the 
   `python version <https://github.com/tomerfiliba/agnos/blob/master/libagnos/python/src/agnos/packers.py>`_.


``Transports`` and ``TransportFactory``
---------------------------------------
Since every programming language has its own concept of how IO-related APIs should
look like (especially network IO), and because they have varying degrees of
success in abstracting the operating system's primitives, Agnos defines its own 
"cross-platform cross-language" view of *transports*.

Transports are much like *streams* in most languages, but they include more featuers,
like framing, compression, and transactioning. Agnos attempts that all implementations
of transports loosely follow this interface (but naturally, they implementations differ
according to language's IO layer):

.. code-block:: java

    interface ITransport {
        void close() throws IOException;
        
        // stream-like views
        InputStream getInputStream();
        OutputStream getOutputStream();
        
        // compression
        boolean isCompressionEnabled();
        boolean enableCompression();
        void disableCompression(); 
        
        // read interface
        int beginRead() throws IOException;
        int read(byte[] data, int offset, int len) throws IOException;
        void endRead() throws IOException;
    
        // write interface
        void beginWrite(int seq) throws IOException;
        void write(byte[] data, int offset, int len) throws IOException;
        void restartWrite() throws IOException;
        void endWrite() throws IOException;
        void cancelWrite() throws IOException;
    }

For full details, refer to the `source code 
<https://github.com/tomerfiliba/agnos/blob/master/libagnos/java/src/agnos/transports/ITransport.java>`_.

All implementations of ``libagnos`` must provide ``SocketTransport`` - a transport that
connects to a server over a network socket. This is the most fundamental transport. 
Implementations are encouraged to also provide:

* ``SSLSocketTransport`` - Same as ``SocketTransport`` but operates over 
  `SSL <http://en.wikipedia.org/wiki/Transport_Layer_Security>`_.

* ``ProcessTransport`` - Connect over a socket to a child process; used to implement
  :ref:`doc-libmode`.

* ``HttpClientTransport`` - Connect to an Agnos server behind an HTTP server; used to
  implement :ref:`doc-over-http`.

Other than transports, Agnos also defined *transport factories*: these are used
o the server-side to accept incoming connections and wrap them by a *transport*
object. Transport factories follow the following interface:

.. code-block:: java

    interface ITransportFactory {
        void close() throws IOException;
        ITransport accept() throws IOException;
    }

and all implementations must provide ``SocketTransportFactory`` -- which is the
server-side counterpart of ``SocketTransport``.


Server Side
-----------

``Processor`` and ``ProcessorFactory``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``Processor`` is the server-side entity that handles client requests: it 
dispatches function calls, performs protocol-level commands, etc. The general skeleton
of ``Processors`` is:

.. code-block:: java

    class BaseProcessor {
        protected ITransport transport;
    
        public BaseProcessor(ITransport transport) {
            // ...
        }
        public void close() throws IOException {
            transport.close();
        }
        
        public void process() throws Exception {
            int seq = transport.beginRead();
            int cmdid = (Byte) (Builtin.Int8.unpack(transport));
    
            transport.beginWrite(seq);
    
            switch (cmdid) {
            case CMD_INVOKE:
                processInvoke(seq);
                break;
            case constants.CMD_DECREF:
                processDecref(seq);
                break;
            // ...
            }
            transport.endRead();
            transport.endWrite();
        }
        
        // ...
    }

The ``process()`` method is the heart of the ``Processor`` -- it reads the incoming
request from the client, parses its fields, and dispatches it, according to the 
command's code. The ``BaseProcessor`` class defines all the shared code, and is part
of ``libagnos``, while the ``Processor`` class extends it and defines the per-service
code (generated by the Agnos compiler).

The ``ProcessorFactory`` is simply a factory object that creates a ``Processor``
that's already bound to a ``Transport``. This interface is really short:

.. code-block:: java

    interface IProcessorFactory {
        BaseProcessor create(ITransport transport);
    }

and it's only used by the ``Server`` class, to create new ``Processor`` instances.


Servers
^^^^^^^
Agnos servers are just like all other servers: they listen to a socket, accept
incoming connections, and serve them. The implementation is free to do this
in whatever way it finds best -- for example, if your language comes with a
standard framework to create servers, you may want to use it directly. Otherwise,
you can follow this scheme:

.. code-block:: java

    class BaseServer
    {
        protected IProcessorFactory processorFactory;
        protected ITransportFactory transportFactory;
    
        public BaseServer(IProcessorFactory processorFactory, ITransportFactory transportFactory)
        {
            this.processorFactory = processorFactory;
            this.transportFactory = transportFactory;
        }
    
        public void serve() throws Exception
        {
            while (true) {
                ITransport transport = transportFactory.accept();
                BaseProcessor processor = processorFactory.create(transport);
                serveClient(processor);
            }
        }
    
        protected abstract void serveClient(BaseProcessor processor) throws Exception;
    }

The implementation then defines several concrete classes, such as ``SimpleServer``
(serves a single client at a time), ``SelectingServer`` (uses ``select()`` to juggle
all connected clients), ``ThreadedServer`` (uses a thread per client), 
``ThreadPoolServer`` (uses threads from a thread-pool to serve clients), or the
``ForkingServer`` (forks a child-process per client).

Apart from these servers, that differ only in their CPU attention-span,
Agnos also provides the ``LibraryModeServer``, which implements the server-side
logic required for :ref:`doc-libmode`: it creates a new server socket on a random
port and prints its details to *stdout*, listens to an incoming connections and
serves it. 

Other than these servers, Agnos usually provides a server ``main()`` function,
which parses command-line arguments and starts the appropriate server. In Java
it's provided by the class ``CmdlineServer``, in python by ``agnos.server.server_main()``.
The command-line arguments accepted by this server are covered 
:ref:`here <server-cmdline-args>`.


HeteroMap
---------

The ``HeteroMap`` class implements the :ref:`heteromap type <type-heteromap>`.
It's a heterogeneous map (or dictionary) that maps keys to values. However, unlike
regular maps, it also stores the key and value packers for each key-value pair.
These packers are used to :ref:`serialize <proto-heteromap>` the map.


Client Side: ``Client`` and ``ClientUtils``
-------------------------------------------
The ``ClientUtils`` class contains all the shared code required to implement 
Agnos clients: it contains reference-counting logic, ``getServiceInfo``,
processing of incoming responses, instantiating exceptions, waiting for replies,
etc. 

The ``BaseClient`` class is usually very simple, only forwarding requests to 
``ClientUtils``. It's used as a base class for the ``Client`` class, that's
generated by the Agnos compiler and contains the service's entry points.


.. ###############################################################################################


Source Generator
================
The *source generator*, although very and handy, is not part of the "Agnos specification". 
An Agnos target can manage perfectly well without one, and if fact, it's considered 
a "third-party" convenience utility. However, since this is a developer's guide, the 
material is covered here too. The syntax and modus operandi is defined in depth 
:ref:`in the specifications <doc-srcgen>`, so this part will only describe the
structure of the ``srcgen`` compiler. 

The code can be found at :file:`compier/src/agnos_compiler/pysrcgen` -- this is the
python source generator. It comprises of two parts, for for building the 
`AST <http://en.wikipedia.org/wiki/Abstract_syntax_tree>`_ (``syntree.py``) and
the other (``generator.py``) for generating the :ref:`IDL <doc-idl>`. The generator employs
the `Visitor_pattern <http://en.wikipedia.org/wiki/Visitor_pattern>`_, as is common
in this "line of business".

The syntax parser is responsible for traversing the directory tree, collecting all 
python files and scanning them for special comments. These comments are then concentrated
into a "linear script" forming the IDL. Most of the code is generic, but note that 
the syntax parser is "tailored" for python's syntactic constructs, like automatically
inferring the name of functions, methods, classes and constants, or automaticlaly
inserting docstrings into the IDL. Should you want to port the syntax parser to another
language, you will need to keep that in mind.

.. note::
   The format of the "special comments" should remain the same across languages,
   namely, ``:: @tag arg1 arg2...``. However, the comment element should match
   the language's line comment. In python it would be ``#:: @class foo`` and in 
   Java, C#, C++, and the like, ``//:: @class foo``.
   
   You should only use line comments, and not block-comments, for ``srcgen``'s 
   special comments, to simplify processing.

The generator traverses the AST and produces three files:

* IDL file - the first and foremost purpose of ``srcgen`` is to generate a single IDL
  file from comments spread around a project. This translation is one-to-one with the
  IDL: ``#:: @class foo`` becomes ``<class foo>...</class>`` and so on. 
  
* Service implementation - since ``srcgen`` operates on an existing package, it
  already implements the service, filling in the "glue code". For example, if you
  have in your project::
  
    #:: @func
    #::    @arg a int
    #::    @arg b int
    def foo(a, b):
        return a + b
  
  The service implementation will include the necessary boilerplate, like so::
  
    import mypackage
    # ...
    class Handler(object):
        # ...
        def foo(self, a, b):
            return mypackage.foo(a, b)
        # ...
  
* :ref:`History file <history-file>` - a file associating function IDs to fully-qualified
  function names. This enables the use of older clients with newer servers, as functions
  retain their original IDs.


The command-line tool, ``agnosrc-py``, is located at :file:`compiler/bin`. It's simply
a front-end that accepts command-line arguments and invokes the ``main()`` function
of the generator.








