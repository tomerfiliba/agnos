import java.util.*;
import FeatureTestBindings.*;

public class myserver {
	public static class ClassA implements FeatureTestBindings.IClassA {
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

	public static class ClassB implements FeatureTestBindings.IClassB {
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

	public static class ClassC implements FeatureTestBindings.IClassC {
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

		private List<FeatureTestBindings.IClassA> attr4 = new ArrayList<FeatureTestBindings.IClassA>();

		public List<FeatureTestBindings.IClassA> get_attr4() throws Exception {
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

	public static class Person implements FeatureTestBindings.IPerson {
		private String name;
		private Person father;
		private Person mother;
		private Person spouse;
		private Date date_of_birth;
		private FeatureTestBindings.Address address;

		protected Person(String name, FeatureTestBindings.IPerson father,
				FeatureTestBindings.IPerson mother) {
			this.name = name;
			this.father = (Person) father;
			this.mother = (Person) mother;
			this.address = new FeatureTestBindings.Address(
					FeatureTestBindings.State.TX, "nashville", "woldorf", 1772);
			this.date_of_birth = new Date();
		}

		// attributes
		public String get_name() throws Exception {
			return name;
		}

		public Date get_date_of_birth() throws Exception {
			return date_of_birth;
		}

		public FeatureTestBindings.Address get_address() throws Exception {
			return address;
		}

		public void set_address(FeatureTestBindings.Address value)
				throws Exception {
			address = value;
		}

		public FeatureTestBindings.IPerson get_father() throws Exception {
			return father;
		}

		public FeatureTestBindings.IPerson get_mother() throws Exception {
			return mother;
		}

		public FeatureTestBindings.IPerson get_spouse() throws Exception {
			return spouse;
		}

		// methods
		public void marry(FeatureTestBindings.IPerson partner) throws Exception {
			if (spouse != null) {
				throw new FeatureTestBindings.MartialStatusError(
						"already married", this);
			}
			if (partner.get_spouse() != null) {
				throw new FeatureTestBindings.MartialStatusError(
						"already married", partner);
			}
			if ((mother != null && mother == partner.get_mother())
					|| (father != null && father == partner.get_father())) {
				throw new FeatureTestBindings.MartialStatusError(
						"siblings cannot marry", partner);
			}
			spouse = (Person) partner;
			spouse.spouse = this;
		}

		public void divorce() throws Exception {
			if (spouse == null) {
				throw new FeatureTestBindings.MartialStatusError(
						"does not have a spouse", this);
			}
			spouse.spouse = null;
			spouse = null;
		}

		public Double think(Double a, Double b) throws Exception {
			return a / b;
		}
	}

	public static class Handler implements FeatureTestBindings.IHandler {
		public FeatureTestBindings.RecordB get_record_b() throws Exception {
			return new FeatureTestBindings.RecordB(new Integer(17),
					new Integer(18), new Long(19));
		}

		public FeatureTestBindings.IPerson Person_init(String name,
				FeatureTestBindings.IPerson father,
				FeatureTestBindings.IPerson mother) throws Exception {
			return new Person(name, father, mother);
		}

		public List<FeatureTestBindings.IClassC> get_class_c() throws Exception {
			ClassA[] x1 = { new ClassA(), new ClassA() };
			ClassA[] x2 = { new ClassA() };

			ArrayList<FeatureTestBindings.IClassC> arr = new ArrayList<FeatureTestBindings.IClassC>();
			// arr.add(new ClassC(4, 5, 6.0, Arrays.asList(x1)));
			// arr.add(new ClassC(33, 12, 76.2, Arrays.asList(x2)));

			return arr;
		}

		public FeatureTestBindings.Everything func_of_everything(Byte a,
				Short b, Integer c, Long d, Double e, Boolean f, Date g,
				byte[] h, String i, List j, Map k,
				FeatureTestBindings.Address l, FeatureTestBindings.IPerson m)
				throws Exception {
			return new FeatureTestBindings.Everything(a, b, c, d, e, f, g, h,
					i, j, k, l, m);
		}
	}

	public static void main(String[] args) {
		agnos.Servers.CmdlineServer server = new agnos.Servers.CmdlineServer(
				new FeatureTestBindings.Processor(new Handler()));
		try {
			server.main(args);
		} catch (Exception ex) {
			ex.printStackTrace(System.out);
		}
	}

}
