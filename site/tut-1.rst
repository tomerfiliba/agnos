Part 1: The Environment
=======================

.. note::
   Be sure to have read the :ref:`doc-started` section before rushing into 
   the tutorial. We assume you already have downloaded and installed Agnos
   properly, and that you're familiar with the terminology and basic 
   concepts.

In this section we'll get acquainted with the Agnos tool chain and write a
simple service -- the Calculator -- where the server is implemented in ``java``
and the client in ``python``.
As the name suggests, the Calculator service exposes a small number of 
arithmetic functions. Let's start with writing the :doc:`IDL <idl>` -- open 
up your favorite XML editor (``notepad`` will do) and paste this snippet:

.. code-block:: xml

    <service name="Calculator">
        <typedef name="real" type="float" />
        
        <const name="pi" type="real" value="3.1415926535897" />
        <const name="e" type="real" value="2.7182818284590" />
        
        <func name="add" type="real">
            <doc>add two real (floating point) numbers</doc>
            <arg name="a" type="real" />
            <arg name="b" type="real" />
        </func>

        <func name="mul" type="real">
            <doc>multiply two real (floating point) numbers</doc>
            <arg name="a" type="real" />
            <arg name="b" type="real" />
        </func>

        <record name="Complex">
            <doc>a record that represents a complex number</doc>
            <attr name="real" type="float" />
            <attr name="imag" type="float" />
        </record>
    
        <func name="cadd" type="Complex">
            <doc>add two complex numbers</doc>
            <arg name="a" type="Complex" />
            <arg name="b" type="Complex" />
        </func>

        <func name="cmul" type="Complex">
            <doc>multiply two complex numbers</doc>
            <arg name="a" type="Complex" />
            <arg name="b" type="Complex" />
        </func>
    </service>

Save under the name ``calculator.xml`` and place it somewhere accessible.

This little :doc:`IDL <idl>` is self-explanatory: we have a ``typedef`` (because
we prefer the name ``real`` over ``float``), two constants, a record that 
defines what a complex number is, and four functions -- two for adding and 
multiplying real numbers, and two for adding and multiplying complex numbers. 

Creating the JAR
----------------
Open a shell and type ::

  $ agnosc -t java -o src calculator.xml 
  $ find -type f
  ./src/Calculator/server_bindings/Calculator.java
  ./src/Calculator/client_bindings/Calculator.java
  ./src/Calculator_server.java.stub
  ./calculator.xml

As you can see, :ref:`tool-agnosc` has generated server bindings, client bindings,
and a server stub (which will be discussed later). You can now use your 
favorite build system (`ant <http://ant.apache.org>`_, 
`scons <http://www.scons.org/>`_, etc.) to build a ``jar`` out of these. I'm
going to do it the good old way, for the sake of simplicity::  

   $ mkdir classes
   $ javac -cp /PATH/TO/agnos.jar -d classes src/Calculator/server_bindings/Calculator.java \
          src/Calculator/client_bindings/Calculator.java
   $ jar -cf CalculatorBindings.jar -C classes Calculator
   $ rm -rf classes

.. note::
   ``/PATH/TO/agnos.jar`` is the location where you downloaded ``agnos.jar``.
   You can either put it in the java *class path*, so the compiler would know 
   where to find it automatically, or specify it explicitly.

Voila! You now have ``CalculatorBindings.jar``, which is what we wanted. The
source files are no longer of use to us, and you may safely delete them::

   $ rm -rf src/Calculator

Compiled Bindings
^^^^^^^^^^^^^^^^^
Future versions of Agnos will support automatically compiling the generated 
bindings for you, so you'll end up with a ``jar``/``dll`` directly. It would
be something in the spirit of ::

  $ agnosc -t java --gen-jar --agnos_jar=/PATH/TO/agnos.jar idlfile.xml


Implementing the Server
-----------------------
Open up you favorite IDE and create a new project, say, ``MyCalculator``.
Copy the generated stub (``src/Calculator_server.java.stub``) into the project,
and of course, remove the ``.stub`` extension. You will also need to add
references to ``agnos.jar`` and ``CalculatorBindings.jar``, and we're ready 
to go. The stub should look like this:

.. code-block:: java

    // ... several imports
    import Calculator.server_bindings.Calculator;
    
    public class ServerStub
    {
        // handler
        public static class Handler implements Calculator.IHandler
        {
            public Double mul(Double a, Double b) throws Exception
            {
                // implement me
            }
            
            public Double add(Double a, Double b) throws Exception
            {
                // implement me
            }
            
            public Calculator.Complex cmul(Calculator.Complex a, Calculator.Complex b) throws Exception
            {
                // implement me
            }
            
            public Calculator.Complex cadd(Calculator.Complex a, Calculator.Complex b) throws Exception
            {
                // implement me
            }
        }
        
        // main
        public static void main(String[] args)
        {
            CmdlineServer server = new CmdlineServer(new Calculator.ProcessorFactory(new Handler()));
            try
            {
                server.main(args);
            }
            catch (Exception ex)
            {
                ex.printStackTrace(System.err);
            }
        }
    }
 
Note that the ``main()`` method is already filled in -- we only need to take
care of three things:
* Rename the class to ``MyCalculator``
* Implement classes (not relevant to our example)
* Implement the handler

.. note::
   In order to reduce the number of generated files, ``agnosc`` uses a compact
   but rather nonstandard code layout. Instead of creating a separate source 
   file for each class -- classes are simply nested. This should be of little
   concern to you, the programmer.
   
   In the generated stub, however, you can feel free to move each class to
   a file of its own. In this tutorial, we'll stick with the nested layout.

Let's now implement the handler: 

.. code-block:: java

    public static class Handler implements Calculator.IHandler
    {
        public Double mul(Double a, Double b) throws Exception
        {
            return a + b;
        }
        
        public Double add(Double a, Double b) throws Exception
        {
            return a * b;
        }
        
        public Calculator.Complex cmul(Calculator.Complex a, Calculator.Complex b) throws Exception
        {
            return new Calculator.Complex(a.real * b.real - a.imag * b.imag, 
                a.real * b.imag + a.imag * b.real);
        }
        
        public Calculator.Complex cadd(Calculator.Complex a, Calculator.Complex b) throws Exception
        {
            return new Calculator.Complex(a.real + b.real, a.imag + b.imag);
        }
    }

And we're ready to go: you can now compile and launch the project. Note that 
it won't run without the necessary command-line arguments: the CmdlineServer
defaults to 'simple mode', where it takes a port number on which it listens.
Set the command line to ``-p 34567`` (or any other available port) and run...
it's a server, so don't expect to see anything printed to the screen.


Writing a Simple Client
-----------------------
We'll now move to writing a simple client in ``python``. Writing one in 
``java`` follows a very similar procedure, albeit more verbose.
Return to the shell, and now run::

   $ agnosc -t python calculator.xml

This would generate ``Calculator_bindings.py`` in the current directory. 
Having our server running in the background, we can launch ``python`` and
type: 

.. code-block:: python

    # import the bindings
    >>> import Calculator_bindings
    
    # create a client by connecting to the server
    >>> c = Calculator_bindings.Client.connect("localhost", 34567)
    
    # and we can start using the client's functions right away
    >>> c.add(5,7)
    12.0
    >>> c.mul(5,7)
    35.0
    
    # create two complex numbers
    >>> n1 = Calculator_bindings.Complex(17,3)
    >>> n2 = Calculator_bindings.Complex(4,-6)
    
    # and we can operate on them, just as well
    >>> c.cadd(n1,n2)
    Complex(21.0, -3.0)
    
    >>> n3 = c.cmul(n1,n2)
    >>> n3
    Complex(86.0, -90.0)

It's as simple as that.













