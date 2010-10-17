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

The command line utility that does the magic is ``agnosc-py``.


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
  #::    @arg name=filename type=string
  #::    @arg name=mode type=FileMode
  def openLocalFile(filename, mode):
      if mode == FileMode.R:
          return File(open(filename, "r"))
      elif mode == FileMode.W:
          return File(open(filename, "w"))
      else:
          raise InvalidMode("given %r" % (mode,))


Specification
=============

The format is pretty simple, and derives of the syntax of ``python``


















