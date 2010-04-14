import java.util.*;
import java.io.*;
import RemoteFiles.Types.*;
import RemoteFiles.Service.*;

public class myclient
{
	public static void main(String[] args)
	{
		try {
			Client c = new Client(
					new agnos.Servers.SocketTransport("localhost", 17732));
			
			try {
				FileProxy f = c.open("/tmp/foo", "w");
				System.out.println("f = " + f);
				f.write("hello world".getBytes());

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
				System.out.println("copy = " + new String(data));
				
				System.out.println("client finished successfully");

			} finally {
				c.close();
			}
		} catch (Exception ex) {
			ex.printStackTrace();
		}
	}
}


