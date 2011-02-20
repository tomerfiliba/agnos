using System;
using System.Collections;
using Agnos;
using FeatureTestBindings.ClientBindings;


public class myclient 
{
	public static void Main(string[] args) 
	{
		foreach(string item in args) {
			Console.WriteLine(item);
		}

        System.Threading.Thread.Sleep(2000);
		
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
		
		System.Console.WriteLine("test passed!");
	}
}