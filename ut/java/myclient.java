import java.util.*;
import java.io.*;
import RemoteFiles.*;

public class myclient
{
	public static void main(String[] args)
	{
		try {
			Service.Client c = new Service.Client(
					new agnos.Servers.SocketTransport("localhost", 17732));
			
			try {
				Types.FileProxy f = c.open("/tmp/foo", "w");
				System.out.println("f = " + f);
				byte[] buf = {1,2,3,4,5};
				f.write(buf);

				try {
					f.flush();
				} catch (Types.UnderlyingIOError exc) {
					System.out.println("got " + exc + " -- as expected");
				}
				
				System.out.println("client finished");

			} finally {
				c.close();
			}
		} catch (Exception ex) {
			ex.printStackTrace();
		}
	}
}

/*
 * c = RemoteFiles.Client.connect("localhost", 17731) f = c.open("/tmp/foo",
 * "w") print f f.write("hello world") s = f.stat() print s try: f.read(10)
 * except RemoteFiles.UnderlyingIOError, ex: print ex f.close() try:
 * f.write("dlrow olleh") except agnos.GenericError, ex: print ex
 * 
 * f1 = c.open("/tmp/foo", "r") f2 = c.open("/tmp/foo2", "w") c.copy(f1, f2)
 * f1.close() f2.close()
 * 
 * f2 = c.open("/tmp/foo2", "r") data = f2.read(100) print "copy = %r" % (data,)
 */

