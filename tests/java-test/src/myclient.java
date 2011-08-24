import java.util.*;
import agnos.util.HeteroMap;
import FeatureTest.client_bindings.FeatureTest;


public class myclient
{
	public static void main(String[] args)
	{
		String host = args[0];
		int port = Integer.parseInt(args[1]);

		try {
			FeatureTest.Client conn = FeatureTest.Client.connectSock(host, port);
			test(conn);
		} catch (Exception ex) {
			ex.printStackTrace(System.out);
			System.exit(1);
		}
	}

	protected static void test(FeatureTest.Client conn)
			throws Exception
	{
		conn.assertServiceCompatibility();
		
		FeatureTest.PersonProxy eve = conn.Person.init("eve", null,
				null);
		FeatureTest.PersonProxy adam = conn.Person.init("adam", null,
				null);
		eve.marry(adam);
		FeatureTest.PersonProxy cain = conn.Person.init("cain", adam,
				eve);

		if (!cain.get_name().equals("cain")) {
			throw new Exception("cain is not the name");
		}

		try {
			adam.marry(eve);
		} catch (FeatureTest.MartialStatusError ex) {
			// okay
		}

		double thought = adam.think(new Double(17), new Double(3))
				.doubleValue();
		if (thought != (17 / 3.0)) {
			throw new Exception("adam thinks wrong: " + thought);
		}

		try {
			adam.think(new Double(17), new Double(0));
		} catch (agnos.protocol.GenericException ex) {
			// okay
		}

		HeteroMap info = conn.getServiceInfo(agnos.protocol.constants.INFO_SERVICE);
		if (!info.get("SERVICE_NAME").equals("FeatureTest")) {
			throw new Exception("wrong service name: "
					+ info.get("SERVICE_NAME"));
		}

		info = conn.getServiceInfo(agnos.protocol.constants.INFO_FUNCTIONS);
		for (Map.Entry e : info.entrySet()) {
			System.out.println(e.getKey().toString() + " = "
					+ e.getValue().toString());
		}
		
		byte[] barr = {(byte)0xff, (byte)0xee, (byte)0xaa, (byte)0xbb};
		List<Double> lst = new ArrayList<Double>();
		lst.add(1.3);
		lst.add(FeatureTest.pi);
		lst.add(4.4);
		Set<Integer> hs = new HashSet<Integer>();
		hs.add(18);
		hs.add(19);
		hs.add(20);
		Map<Integer, String> hm = new HashMap<Integer, String>();
		hm.put(34, "foo");
		hm.put(56, "bar");
		FeatureTest.Address adr = new FeatureTest.Address(FeatureTest.State.NY, "albany", "foobar drive", 1772);
		
		FeatureTest.Everything everything = conn.func_of_everything(
				new Byte((byte)1), new Short((short)2), new Integer(3), new Long(4), new Double(5.5), 
				new Boolean(true), new Date(), barr, "hello world", lst, hs, hm, adr, 
				eve, FeatureTest.MyEnum.C);
		
		if (everything.some_int32.intValue() != 3) {
			throw new Exception("expected 'some_int32' to be 3" + everything.some_int32);
		}
		

		System.out.println("okay");
	}
}
