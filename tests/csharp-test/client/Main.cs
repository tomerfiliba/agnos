using System;
using System.Collections;
using System.Collections.Generic;
using Agnos;
using FeatureTestBindings.ClientBindings;


public class myclient 
{
	public static void Main(string[] args) 
	{
		foreach(string item in args) {
			Console.WriteLine(item);
		}

        //System.Threading.Thread.Sleep(2000);
		
		string host = args[0];
		int port = int.Parse(args[1]);

		using (FeatureTest.Client conn = FeatureTest.Client.ConnectSock(host, port)) {
		    test(conn);
        }
	}

	protected static void test(FeatureTest.Client conn)
	{
		conn.AssertServiceCompatibility();
	
		var eve = conn.Person.init("eve", null,	null);
		var adam = conn.Person.init("adam", null, null);
		eve.marry(adam);
		var cain = conn.Person.init("cain", adam, eve);
		if (cain.name != "cain") {
			throw new Exception("cain is not the name");
		}

        bool succ = true;
		try {
			adam.marry(eve);
		} catch (FeatureTest.MartialStatusError) {
			// okay
            succ = false;
		}

        if (succ) {
            throw new Exception("an exception should have been thrown!");
        }
		
		double thought = adam.think(17, 3.0);
        if (thought != (17/3.0)) {
			throw new Exception("adam thinks wrong: " + thought);
        }
        
        try {
			adam.think(17, 0);
		} catch (Agnos.GenericException) {
			// okay
		}

		var info = conn.GetServiceInfo(Agnos.Protocol.INFO_SERVICE);
		if ((String)info["SERVICE_NAME"] != "FeatureTest") {
			throw new Exception("wrong service name: " + info["SERVICE_NAME"]);
		}
		
		info = conn.GetServiceInfo(Agnos.Protocol.INFO_FUNCTIONS);
		foreach (DictionaryEntry e in info) {
			System.Console.WriteLine("{0} = {1}", e.Key, e.Value);
		}
		
		byte[] barr = {(byte)0xff, (byte)0xee, (byte)0xaa, (byte)0xbb};
		IList<double> lst = new List<double>();
		lst.Add(1.3);
		lst.Add(FeatureTest.pi);
		lst.Add(4.4);
		ICollection<int> hs = new HashSet<int>();
		hs.Add(18);
		hs.Add(19);
		hs.Add(20);
		IDictionary<int, string> hm = new Dictionary<int, string>();
		hm[34] = "foo";
		hm[56] = "bar";
		FeatureTest.Address adr = new FeatureTest.Address(FeatureTest.State.NY, "albany", "foobar drive", 1772);
		
		
		FeatureTest.Everything everything = conn.func_of_everything(
				(byte)1, (short)2, 3, (long)4, 5.5, true, new DateTime(), barr, 
				"hello world", lst, hs, hm, adr, eve, FeatureTest.MyEnum.C);
		
		if (everything.some_int32 != 3) {
			throw new Exception("expected 'some_int32' to be 3" + everything.some_int32);
		}

		HeteroMap hm1 = new HeteroMap();
		hm1["x"] = "y";
		HeteroMap hm2 = conn.hmap_test(1999, hm1);
		if ((int)hm2["a"] != 1999) {
			throw new Exception("expected 'a' to be 1999; " + hm2["a"]);
		}
				
		System.Console.WriteLine("test passed!");
	}
}