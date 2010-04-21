using System;
using System.Text;
using Agnos;
using RemoteFilesStub;


namespace client_test
{
	class MainClass
	{
		public static void Main(string[] args)
		{
			using (RemoteFiles.Client c = new RemoteFiles.Client(
					new Agnos.Transports.SocketTransport("localhost", 17735)))
			{
				RemoteFiles.FileProxy f = c.open("/tmp/foo", "w");
				System.Console.WriteLine("f = {0}", f);
				/*f.write(Text."hello world".getBytes());

				System.out.println("filename = " + f.get_filename());
				System.out.println("stat = " + f.stat());
				
				boolean got_exc = false;
				try {
					f.flush();
				} catch (UnderlyingIOError exc) {
					got_exc = true;
					System.out.println("matched: " + exc);
				}
				assert(got_exc);
				
				try {
					// should cause NullPointer, since opened for writing
					f.read(10); 
				}
				catch (agnos.Protocol.GenericError exc) {
					System.out.println("matched: " + exc);
				}
				
				f.close();

				FileProxy f1 = c.open("/tmp/foo", "r");
				FileProxy f2 = c.open("/tmp/foo2", "w");
				c.copy(f1, f2);
				f1.close();
				f2.close();

				f2 = c.open("/tmp/foo2", "r");
				byte[] data = f2.read(100);
				System.out.println("copy = " + new String(data));*/
				
				System.Console.WriteLine("client finished successfully");
			}
		}
	}
}