``srcgen``
==========
``srcgen`` (short for ``source generator``) is part of the Agnos :doc:`toolchain`,
and its purpose is to minimize messing with XMLs, which are hard for human-editing.
Instead, you can place special comments embedded in your code for ``srcgen``, 
which reads them and generates the IDL XML for you, as well as automatically 
generating the server implementation, which is tightly-coupled to your code.

.. note::
  At the moment, ``srcgen`` works only on ``python`` packages. ``Java``, ``C#`` 
  and ``C++`` versions are planned for future releases.

The command line utility that does the magic is :ref:`agnosrc-py`.


Let's See Some Code
===================
Suppose you want to expose and remote-files service, `like the one you've 
seen <teaser>`_. Instead of first writing the IDL and then implementing the
server, you can do it the other way -- write the implementation, and annotate
the parts that are to be exposed.

.. code-block:: python

  #:: @service RemoteFiles

  #:: @enum
  class FileMode:
      #:: @member
      R = 1
      #:: @member
      W = 2

  #:: @class
  class File(object):
      def __init__(self, fileobj):
          self._file = fileobj
      
      #:: @method type=buffer
      #::    @arg name=count type=int32
      def read(self, count):
          return self._file.read(count)
      
      #:: @method type=void
      #::    @arg name=data type=buffer
      def write(self, data):
          return self._file.write(data)
      
      #:: @method type=void
      def close(self):
          self._file.close()

  #:: @exception
  class InvalidMode(Exception):
      #:: @attr name=info type=str
      
      def __init__(self, info):
          self.info = info

  #:: @func type=File
  #::    this function opens a local file and returns a File instance
  #::    which can be used by the client
  #::
  #::    @arg filename type=string
  #::    @arg mode type=FileMode
  def openLocalFile(filename, mode):
      if mode == FileMode.R:
          return File(open(filename, "r"))
      elif mode == FileMode.W:
          return File(open(filename, "w"))
      else:
          raise InvalidMode("given %r" % (mode,))


Specification
=============

The format is pretty simple: it is *indentation-based* (like ``python``),
begins with the language's line comment (e.g., ``#`` or ``//``), followed by
two colons (``::``), after which comes text. If the first token starts with
a ``@`` symbol, it's considered a tag, otherwise it's processed as
plain text (for documentation purposes).

The format of a command is as follows::

  #:: @tag [NAME] [arg1=val1] [arg2=val2] ...

The first token after the tag (also called *command*) may provide the name 
of the entity. If it is not given, ``srcgen`` uses the name of the programmatic 
entity (i.e., it parses the lines following the comment and looks for the 
function's or class' name). Then, any number of variables in the form of 
key=value pairs may follow.
The arguments depend on the command, and are essentially the same as the XML
format. For information about the exact arguments each command takes, refer
to the :doc:`IDL reference<idl>`.

Note that the arguments are whitespace-seperated. For that reason, neither
the name nor the value of the argument can contain whitespace, but as ``srcgen``
only really needs to process programming-language tokens, this shouldn't 
pose a problem.

Just like XML, a command may have sub-elements under it, namely sub-commands 
and documentation elements These are created by simply indenting them further
than the command itself::

  #:: @command foo=bar spam=bacon
  #::    this is a documentation line. empty lines are ignored
  #::
  #::    @subcommand omlette=du_fromage
  #::        this is another documentation line
  #::        and even a second line

Notes
-----

Every "project" (usually the root-package) that ``srcgen`` processes, must define
a ``@service`` tag exactly once. This tag serves as the root node of the XML
document, and specifies the service' name and versions. It is a wise practice
to place some documentation under this tag, describing the service.

Every module (usually a sub-package or file) may contain a ``@module`` tag,
specifying the name of the module (for binding purposes), and an optional 
namespace. If a namespace is given, it is used for all the constants and 
functions in the module. Using namespace is a good practice, as it allows you
to expose two functions of the same name.

Function-level Versioning
-------------------------
TODO




















