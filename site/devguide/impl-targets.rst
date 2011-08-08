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
as a separate project. It uses `context managers <http://docs.python.org/reference/compound_stmts.html#the-with-statement>`_
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
of effort has been put into this design, and following it may save you considerable time.

Packers
-------
TBD

Protocol
--------
TBD

Processor and ProcessorFactory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TBD

Client and ClientUtils
^^^^^^^^^^^^^^^^^^^^^^
TBD

Servers
-------
TBD

Transports and Transport Factories
----------------------------------
TBD



.. ###############################################################################################



Source Generator
================
The *source generator*, although very and handy, is not part of the "Agnos specification". 
An Agnos target can manage perfectly without one, and if fact, it's considered a "third-party"
convenience utility. However, since this is a developer's guide, the material is covered 
here too.














