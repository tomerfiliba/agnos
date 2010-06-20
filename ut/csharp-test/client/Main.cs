using System;
using Agnos;
using FeatureTestBindings;


public class myclient {
	public static void Main(string[] args) 
	{
		string host = args[0];
		int port = int.Parse(args[1]);

		FeatureTest.Client conn = new FeatureTest.Client(
				new Agnos.Transports.SocketTransport(host, port));
		test(conn);
	}

	protected static void test(FeatureTest.Client conn)
	{
		FeatureTest.PersonProxy eve = conn.Person.init("eve", null,
				null);
		FeatureTest.PersonProxy adam = conn.Person.init("adam", null,
				null);
		eve.marry(adam);
		FeatureTest.PersonProxy cain = conn.Person.init("cain", adam,
				eve);
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
		
		System.Console.WriteLine("test passed!");
	}
}