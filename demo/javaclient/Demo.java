import java.util.*;
import MextraBindings.*;


public class Demo
{
	public static void main(String args[])
	{
		String host = args[0];
		int port = Integer.parseInt(args[1]);

		try {
			MextraBindings.Client conn = MextraBindings.Client.connectSock(host, port);
			//MextraBindings.Client conn = MextraBindings.Client.connectProc("./mextra_server.py")
			doStuff(conn);
		} catch (Exception ex) {
			ex.printStackTrace(System.out);
		}
	}
	
	public static void doStuff(MextraBindings.Client conn) throws Exception
	{
		System.out.println(conn.getServiceInfo(agnos.Protocol.INFO_GENERAL));
		
		MextraBindings.StorageSystemProxy sys = conn.get_system();
		System.out.println(sys);
		
		List racks = sys.get_racks();
		MextraBindings.RackProxy rack = (MextraBindings.RackProxy)racks.get(0);
		System.out.println("this rack: " + rack.get_compid());
		
		MextraBindings.PoolProxy pool = (MextraBindings.PoolProxy)sys.get_pools().get(0);
		System.out.println("pool name: " + pool.get_name());
		System.out.println("used size: " + pool.get_used_size());
		MextraBindings.IVolume vol = pool.create_volume("moshiko", new Long(18290));
		System.out.println("used size after creating a volume: " + pool.get_used_size());
		
		try {
			vol.resize(new Long(99));
		} catch (MextraBindings.VolSizeError ex) {
			System.out.println("oops: " + ex);
		}

		vol.resize(new Long(999999));
		System.out.println("used size after growing volume: " + pool.get_used_size());
	}
}
