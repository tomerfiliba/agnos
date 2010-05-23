using System;
using System.Text;
using Agnos;
using RemoteFilesBindings;


namespace client_test
{
	class MainClass
	{
		public static void Main(string[] args)
		{
			using (RemoteFiles.Client c = new RemoteFiles.Client(
					new Agnos.Transports.SocketTransport("localhost", 17735)))
			{
				RemoteFiles.FileProxy f = c.open("foo", "w");
				System.Console.WriteLine("f = {0}", f);
				f.write(new System.Text.ASCIIEncoding().GetBytes("hello world"));

				System.Console.WriteLine("filename = {0}", f.filename);
				System.Console.WriteLine("stat = {0}", f.stat());
				
				bool got_exc = false;
				try {
					f.flush();
				} catch (RemoteFiles.UnderlyingIOError exc) {
					got_exc = true;
					System.Console.WriteLine("matched: " + exc);
				}
			    if (!got_exc) {
                    throw new Exception("did not throw exception!");
                }

				try {
					// should cause NullPointer, since opened for writing
					f.read(10); 
				}
				catch (Agnos.GenericException exc) {
					System.Console.WriteLine("matched: " + exc);
				}
				
				f.close();

                RemoteFiles.FileProxy f1 = c.open("foo", "r");
                RemoteFiles.FileProxy f2 = c.open("foo2", "w");
				c.copy(f1, f2);
				f1.close();
				f2.close();

				f2 = c.open("foo2", "r");
				byte[] data = f2.read(100);
				System.Console.WriteLine("copy = {0}", new System.Text.ASCIIEncoding().GetString(data));
				
				System.Console.WriteLine("client finished successfully");
			}
		}
	}
}