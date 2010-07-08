import java.util.*;
import FeatureTestBindings.*;


public class myclient
{
	public static void main(String[] args)
	{
		String host = args[0];
		int port = Integer.parseInt(args[1]);

		try {
			FeatureTestBindings.Client conn = new FeatureTestBindings.Client(
					new agnos.Transports.SocketTransport(host, port));
			test(conn);
		} catch (Exception ex) {
			ex.printStackTrace(System.out);
			System.exit(1);
		}
	}

	protected static void test(FeatureTestBindings.Client conn)
			throws Exception
	{
		FeatureTestBindings.PersonProxy eve = conn.Person.init("eve", null,
				null);
		FeatureTestBindings.PersonProxy adam = conn.Person.init("adam", null,
				null);
		eve.marry(adam);
		FeatureTestBindings.PersonProxy cain = conn.Person.init("cain", adam,
				eve);

		if (!cain.get_name().equals("cain")) {
			throw new Exception("cain is not the name");
		}

		try {
			adam.marry(eve);
		} catch (FeatureTestBindings.MartialStatusError ex) {
			// okay
		}

		double thought = adam.think(new Double(17), new Double(3))
				.doubleValue();
		if (thought != (17 / 3.0)) {
			throw new Exception("adam thinks wrong: " + thought);
		}

		try {
			adam.think(new Double(17), new Double(0));
		} catch (agnos.Protocol.GenericException ex) {
			// okay
		}

		agnos.HeteroMap info = conn.getServiceInfo(agnos.Protocol.INFO_GENERAL);
		if (!info.get("SERVICE_NAME").equals("FeatureTest")) {
			throw new Exception("wrong service name: " + info.get("SERVICE_NAME"));
		}
		
		info = conn.getServiceInfo(agnos.Protocol.INFO_FUNCCODES);
		for(Map.Entry e : info.entrySet()) {
			System.out.println(e.getKey().toString() + " = " + e.getValue().toString());
		}

		System.out.println("okay");
	}
}
