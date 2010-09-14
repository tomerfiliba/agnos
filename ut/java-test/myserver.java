import java.util.*;
import FeatureTest.server_bindings.*;

public class myserver {
	public static class ClassA implements FeatureTest.IClassA {
		private Integer val = new Integer(17);

		public Integer get_attr1() throws Exception {
			return val;
		}

		public void set_attr1(Integer value) throws Exception {
			val = value;
		}

		public Integer get_attr2() throws Exception {
			return new Integer(199);
		}

		public void set_attr2(Integer value) throws Exception {
		}

		// methods
		public Integer method1(String a, Boolean b) throws Exception {
			int v = b ? 7 : 3;
			return new Integer(Integer.parseInt(a) + v);
		}
	}

	public static class ClassB implements FeatureTest.IClassB {
		private Integer val = new Integer(17);
		private Double val3 = new Double(17.77);

		public Integer get_attr1() throws Exception {
			return val;
		}

		public void set_attr1(Integer value) throws Exception {
			val = value;
		}

		public Integer get_attr2() throws Exception {
			return new Integer(211);
		}

		public void set_attr2(Integer value) throws Exception {
		}

		public Double get_attr3() throws Exception {
			return val3;
		}

		public void set_attr3(Double value) throws Exception {
			val3 = value;
		}

		// methods
		public Integer method1(String a, Boolean b) throws Exception {
			int v = b ? 7 : 3;
			return new Integer(Integer.parseInt(a) + v);
		}

		public Integer method2(String a, Boolean b) throws Exception {
			int v = b ? 99 : 33;
			return new Integer(Integer.parseInt(a) + v);
		}
	}

	public static class ClassC implements FeatureTest.IClassC {
		private Integer val = new Integer(17);
		private Double val3 = new Double(17.77);

		public Integer get_attr1() throws Exception {
			return val;
		}

		public void set_attr1(Integer value) throws Exception {
			val = value;
		}

		public Integer get_attr2() throws Exception {
			return new Integer(399);
		}

		public void set_attr2(Integer value) throws Exception {
		}

		public Double get_attr3() throws Exception {
			return val3;
		}

		public void set_attr3(Double value) throws Exception {
			val3 = value;
		}

		private List<FeatureTest.IClassA> attr4 = new ArrayList<FeatureTest.IClassA>();

		public List<FeatureTest.IClassA> get_attr4() throws Exception {
			return attr4;
		}

		// methods
		public Integer method1(String a, Boolean b) throws Exception {
			int v = b ? 7 : 3;
			return new Integer(Integer.parseInt(a) + v);
		}

		public Integer method2(String a, Boolean b) throws Exception {
			int v = b ? 99 : 33;
			return new Integer(Integer.parseInt(a) + v);
		}

		public Integer method3(String a, Boolean b) throws Exception {
			int v = b ? 22 : -22;
			return new Integer(Integer.parseInt(a) + v);
		}
	}

	public static class Person implements FeatureTest.IPerson {
		private String name;
		private Person father;
		private Person mother;
		private Person spouse;
		private Date date_of_birth;
		private FeatureTest.Address address;

		protected Person(String name, FeatureTest.IPerson father,
				FeatureTest.IPerson mother) {
			this.name = name;
			this.father = (Person) father;
			this.mother = (Person) mother;
			this.address = new FeatureTest.Address(
					FeatureTest.State.TX, "nashville", "woldorf", 1772);
			this.date_of_birth = new Date();
		}

		// attributes
		public String get_name() throws Exception {
			return name;
		}

		public Date get_date_of_birth() throws Exception {
			return date_of_birth;
		}

		public FeatureTest.Address get_address() throws Exception {
			return address;
		}

		public void set_address(FeatureTest.Address value)
				throws Exception {
			address = value;
		}

		public FeatureTest.IPerson get_father() throws Exception {
			return father;
		}

		public FeatureTest.IPerson get_mother() throws Exception {
			return mother;
		}

		public FeatureTest.IPerson get_spouse() throws Exception {
			return spouse;
		}

		// methods
		public void marry(FeatureTest.IPerson partner) throws Exception {
			if (spouse != null) {
				throw new FeatureTest.MartialStatusError(
						"already married", this);
			}
			if (partner.get_spouse() != null) {
				throw new FeatureTest.MartialStatusError(
						"already married", partner);
			}
			if ((mother != null && mother == partner.get_mother())
					|| (father != null && father == partner.get_father())) {
				throw new FeatureTest.MartialStatusError(
						"siblings cannot marry", partner);
			}
			spouse = (Person) partner;
			spouse.spouse = this;
		}

		public void divorce() throws Exception {
			if (spouse == null) {
				throw new FeatureTest.MartialStatusError(
						"does not have a spouse", this);
			}
			spouse.spouse = null;
			spouse = null;
		}

		public Double think(Double a, Double b) throws Exception {
			return a / b;
		}
	}

	public static class Handler implements FeatureTest.IHandler {
		public FeatureTest.RecordB get_record_b() throws Exception {
			return new FeatureTest.RecordB(new Integer(17),
					new Integer(18), new Long(19));
		}

		public FeatureTest.IPerson Person_init(String name,
				FeatureTest.IPerson father,
				FeatureTest.IPerson mother) throws Exception {
			return new Person(name, father, mother);
		}

		public List<FeatureTest.IClassC> get_class_c() throws Exception {
			ClassA[] x1 = { new ClassA(), new ClassA() };
			ClassA[] x2 = { new ClassA() };

			ArrayList<FeatureTest.IClassC> arr = new ArrayList<FeatureTest.IClassC>();
			// arr.add(new ClassC(4, 5, 6.0, Arrays.asList(x1)));
			// arr.add(new ClassC(33, 12, 76.2, Arrays.asList(x2)));

			return arr;
		}

		public FeatureTest.Everything func_of_everything(Byte a,
				Short b, Integer c, Long d, Double e, Boolean f, Date g,
				byte[] h, String i, List<Double> j, Set<Integer> k, Map<Integer, String> l,
				FeatureTest.Address m, FeatureTest.IPerson n)
				throws Exception {
			return new FeatureTest.Everything(a, b, c, d, e, f, g, h,
					i, j, k, l, m, n);
		}
	}

	public static void main(String[] args) {
		agnos.Servers.CmdlineServer server = new agnos.Servers.CmdlineServer(
				new FeatureTest.ProcessorFactory(new Handler()));
		try {
			server.main(args);
		} catch (Exception ex) {
			ex.printStackTrace(System.out);
		}
	}

}
