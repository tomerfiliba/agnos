using System;
using System.Collections;
using Agnos;
using FeatureTestBindings;


public class myclient {
	public static void Main(string[] args) 
	{
		string host = args[0];
		int port = int.Parse(args[1]);

		FeatureTest.Client conn = FeatureTest.Client.ConnectSock(host, port);
		test(conn);
	}

	protected static void test(FeatureTest.Client conn)
	{
		var eve = conn.Person.init("eve", null,	null);
		var adam = conn.Person.init("adam", null, null);
		eve.marry(adam);
		var cain = conn.Person.init("cain", adam, eve);
		if (cain.name != "cain") {
			throw new Exception("cain is not the name");
		}

		try {
			adam.marry(eve);
		} catch (FeatureTest.MartialStatusError) {
			// okay
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

		var info = conn.GetServiceInfo(Agnos.Protocol.INFO_GENERAL);
		if ((String)info["SERVICE_NAME"] != "FeatureTest") {
			throw new Exception("wrong service name: " + info["SERVICE_NAME"]);
		}
		
		info = conn.GetServiceInfo(Agnos.Protocol.INFO_FUNCCODES);
		foreach (DictionaryEntry e in info) {
			System.Console.WriteLine("{0} = {1}", e.Key, e.Value);
		}
		
		System.Console.WriteLine("test passed!");
	}
}