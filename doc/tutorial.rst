.. _tutorial1:

Tutorial
========

::

  $ agnosc -t java remotefiles.xml

This generates the directory ``RemoteFiles/`` with java files. 
We'll compile and jar them to ``RemoteFiles.jar`` ::

  $ agnosc -t python remotefiles.xml 

This generates ``RemoteFiles_bindings.py``


Java Server
-----------
.. code-block:: java

  import static agnos.Servers.CmdlineServer;
  import RemoteFiles.server_bindings.RemoteFiles;

  public class Main
  {
      public static class MyFile extends RemoteFiles.IFile
      {
          protected String _name;
          protected FileInputStream fis;
          protected FileOutputStream fos;

          public MyFile(String name, RemoteFiles.FileMode mode) {
              _name = name;
              if (mode == RemoteFiles.FileMode.R) {
                  fis = new FileInputStream(name);
              }
              else if (mode == RemoteFiles.FileMode.W) {
                  fos = new FileOutputStream(name);
              }
              else {
                  throw new IllegalArgumentException("invalid mode");
              }
          }
          public String get_name() {
              return _name;
          }
          public byte[] read(int count) {
              byte[] buf = new buf[count];
              int actual = fis.read(buf, 0, count);
              byte res[] = new byte[actual]
              System.arraycopy(buf, 0, res, 0, actual);
              return res;
          }
          public void write(byte[] data) {
              fos.write(data, 0, data.length);
          }
      }

      public static class Handler implements RemoteFiles.IHandler 
      {
          public RemoteFiles.IFile open(String filename, RemoteFiles.FileMode mode) {
              return new MyFile(filename, mode)
          }
      }

      public static void main(String[] args) {
          CmdlineServer server = new CmdlineServer(new RemoteFiles.ProcessorFactory(new Handler()));
          try {
              server.main(args);
          } catch (Exception ex) {
              ex.printStackTrace(System.out);
          }
      }
  }

