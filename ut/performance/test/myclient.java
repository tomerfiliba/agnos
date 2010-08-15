import java.util.*;
import filesystem.client_bindings.*;


public class myclient
{
	public static void main(String[] args)
	{
		String host = args[0];
		int port = Integer.parseInt(args[1]);

		try {
			filesystem.Client conn = filesystem.Client.connectSock(host, port);
			test(conn);
			System.out.println("okay");
		} catch (Exception ex) {
			ex.printStackTrace(System.out);
			System.exit(1);
		}
	}

	protected static void test(filesystem.Client conn) throws Exception
	{
		conn.assertServiceCompatibility();
		filesystem.FileProxy f = conn.open("/foo/bar.txt", filesystem.FileMode.READWRITE);
		System.out.println("f = " + f);
		
		long total;
		double dt;
		int i;
		Date t0, t1;
		byte[] buf;
		
		System.out.println("==== big chunks (1GB at 512KB chunks) ====");

		total = 0;
		t0 = new Date();
		for (i = 0; i < 2 * 1024; i++) {
			buf = f.read(512*1024);
			total += buf.length;
		}
		t1 = new Date();
		
		dt = t1.getTime() - t0.getTime();
		System.out.println("total bytes: " + total);
		System.out.println("total time (ms): " + dt);
		System.out.println("rate (MB/sec): " + ((total / (1024 * 1024)) / (dt / 1000)));
		
		System.out.println("==== small chunks (1GB at 8KB chunks) ====");

		total = 0;
		t0 = new Date();
		for (i = 0; i < 128 * 1024; i++) {
			buf = f.read(8*1024);
			total += buf.length;
		}
		t1 = new Date();
		
		dt = t1.getTime() - t0.getTime();
		System.out.println("total bytes: " + total);
		System.out.println("total time (ms): " + dt);
		System.out.println("rate (MB/sec): " + ((total / (1024 * 1024)) / (dt / 1000)));
		
		System.out.println("==== invocations ====");
	
		t0 = new Date();
		for (i = 0; i < 100000; i++) {
			buf = f.read(8);
			buf[0] = 19;
			f.write(buf);
			f.seek(new Long(i));
			if (f.tell() != i) {
				throw new Exception("oops");
			}
		}
		t1 = new Date();
		
		dt = t1.getTime() - t0.getTime();
		System.out.println("time for " + (i * 4) + " invocations (ms): " + dt);
		System.out.println("avg per invocation (us): " + ((dt * 1000) / (4 * i)));
	}
}
