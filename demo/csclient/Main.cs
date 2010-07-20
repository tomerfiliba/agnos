using System;
using System.Collections;
using MextraBindings.ClientBindings;


namespace csclient
{
	class MainClass
	{
		public static void Main (string[] args)
		{
			string host = args[0];
			int port = int.Parse(args[1]);
	
			Mextra.Client conn = Mextra.Client.ConnectSock(host, port);
			
			System.Console.WriteLine(conn.GetServiceInfo(Agnos.Protocol.INFO_GENERAL));
			
			var sys = conn.get_system();
			//var v = conn.Volume.create_volume();
			
			System.Console.WriteLine(sys);
			
			var racks = sys.racks;
			System.Console.WriteLine("this rack: {0}", racks[0].compid);
			
			var pool = sys.pools[0];
			System.Console.WriteLine("pool name: {0}", pool.name);
			System.Console.WriteLine("used size: {0}", pool.used_size);
			
			var vol = pool.create_volume("moshiko", 18290);
			System.Console.WriteLine("used size after creating a volume: {0}", pool.used_size);
			
			try {
				vol.resize(99);
			} catch (Mextra.VolSizeError ex) {
				System.Console.WriteLine("oops: {0}", ex);
			}
	
			vol.resize(999999);
			System.Console.WriteLine("used size after growing volume: {0}", pool.used_size);
		}
	}
}
