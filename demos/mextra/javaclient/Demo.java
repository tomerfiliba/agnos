import java.util.*;
import Mextra.client_bindings.*;


public class Demo
{
	public static void main(String args[])
	{
		String host = args[0];
		int port = Integer.parseInt(args[1]);

		try {
			Mextra.Client conn = Mextra.Client.connectSock(host, port);
			doStuff(conn);
		} catch (Exception ex) {
			ex.printStackTrace(System.out);
		}
	}
	
	public static void doStuff(Mextra.Client conn) throws Exception
	{
		System.out.println(conn.getServiceInfo(agnos.Protocol.INFO_SERVICE));
		
		conn.assertServiceCompatibility();
		
		Mextra.StorageSystemProxy sys = conn.get_system();
		System.out.println(sys);
		
		List<Mextra.RackProxy> racks = sys.get_racks();
		System.out.println("this rack: " + racks.get(0).get_compid());
		
		Mextra.PoolProxy pool = sys.get_pools().get(0);
		System.out.println("pool name: " + pool.get_name());
		System.out.println("used size: " + pool.get_used_size());
		Mextra.VolumeProxy vol = pool.create_volume("moshiko", new Long(18290));
		System.out.println("used size after creating a volume: " + pool.get_used_size());
		
		try {
			vol.resize(new Long(99));
		} catch (Mextra.VolSizeError ex) {
			System.out.println("oops: " + ex);
		}

		vol.resize(new Long(999999));
		System.out.println("used size after growing volume: " + pool.get_used_size());
	}
}
