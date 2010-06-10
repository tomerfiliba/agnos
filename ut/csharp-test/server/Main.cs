using System;
using Agnos;
using FeatureTestBindings;
using System.Collections;
using System.Collections.Generic;


public class myserver 
{
	public class ClassA : FeatureTest.IClassA {
		private int val = 17;

		public int attr1 {
			get {
				return val;
			}
		}

		public void set_attr1(int value) {
			val = value;
		}

		public int get_attr2()  {
			return 199;
		}

		public void set_attr2(int value)  {
		}

		// methods
		public int method1(string a, bool b)  {
			int v = b ? 7 : 3;
			return int.Parse(a) + v;
		}
	}
	
	public class ClassB : FeatureTest.IClassB {
		private int val = 17;
		private double val3 = new double(17.77);

		public int get_attr1()  {
			return val;
		}

		public void set_attr1(int value)  {
			val = value;
		}

		public int get_attr2()  {
			return 211;
		}

		public void set_attr2(int value)  {
		}

		public double get_attr3()  {
			return val3;
		}

		public void set_attr3(double value)  {
			val3 = value;
		}

		// methods
		public int method1(string a, bool b)  {
			int v = b ? 7 : 3;
			return int.Parse(a) + v;
		}

		public int method2(string a, bool b)  {
			int v = b ? 99 : 33;
			return int.Parse(a) + v;
		}
	}

	public class ClassC : FeatureTest.IClassC {
		private int val = 17;
		private double val3 = 17.77;

		public int get_attr1()  {
			return val;
		}

		public void set_attr1(int value)  {
			val = value;
		}

		public int get_attr2()  {
			return 399;
		}

		public void set_attr2(int value)  {
		}

		public double get_attr3()  {
			return val3;
		}

		public void set_attr3(double value)  {
			val3 = value;
		}

		private List<FeatureTest.IClassA> attr4 = new ArrayList<FeatureTest.IClassA>();

		public List<FeatureTest.IClassA> get_attr4()  {
			return attr4;
		}

		// methods
		public int method1(string a, bool b)  {
			int v = b ? 7 : 3;
			return int.Parse(a) + v;
		}

		public int method2(string a, bool b)  {
			int v = b ? 99 : 33;
			return int.Parse(a) + v;
		}

		public int method3(string a, bool b)  {
			int v = b ? 22 : -22;
			return int.Parse(a) + v;
		}
	}

	public class Person : FeatureTest.IPerson {
		private string name;
		private Person father;
		private Person mother;
		private Person spouse;
		private Date date_of_birth;
		private FeatureTest.Address address;

		protected Person(string name, FeatureTest.IPerson father,
				FeatureTest.IPerson mother) {
			this.name = name;
			this.father = (Person) father;
			this.mother = (Person) mother;
			this.address = new FeatureTest.Address(
					FeatureTest.State.TX, "nashville", "woldorf", 1772);
			this.date_of_birth = new Date();
		}

		// attributes
		public string get_name()  {
			return name;
		}

		public Date get_date_of_birth()  {
			return date_of_birth;
		}

		public FeatureTest.Address get_address()  {
			return address;
		}

		public void set_address(FeatureTest.Address value)
				 {
			address = value;
		}

		public FeatureTest.IPerson get_father()  {
			return father;
		}

		public FeatureTest.IPerson get_mother()  {
			return mother;
		}

		public FeatureTest.IPerson get_spouse()  {
			return spouse;
		}

		// methods
		public void marry(FeatureTest.IPerson partner)  {
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

		public void divorce()  {
			if (spouse == null) {
				throw new FeatureTest.MartialStatusError(
						"does not have a spouse", this);
			}
			spouse.spouse = null;
			spouse = null;
		}

		public double think(double a, double b)  {
			return a / b;
		}
	}

	public class Handler : FeatureTest.IHandler {
		public FeatureTest.RecordB get_record_b()  {
			return new FeatureTest.RecordB(17, 18, 19);
		}

		public FeatureTest.IPerson Person_init(string name,
				FeatureTest.IPerson father,
				FeatureTest.IPerson mother)  {
			return new Person(name, father, mother);
		}

		public List<FeatureTest.IClassC> get_class_c()  {
			ClassA[] x1 = { new ClassA(), new ClassA() };
			ClassA[] x2 = { new ClassA() };

			ArrayList<FeatureTest.IClassC> arr = new ArrayList<FeatureTest.IClassC>();
			// arr.add(new ClassC(4, 5, 6.0, Arrays.asList(x1)));
			// arr.add(new ClassC(33, 12, 76.2, Arrays.asList(x2)));

			return arr;
		}

		public FeatureTest.Everything func_of_everything(Byte a,
				Short b, int c, Long d, double e, bool f, Date g,
				byte[] h, string i, List j, Map k,
				FeatureTest.Address l, FeatureTest.IPerson m)
				 {
			return new FeatureTest.Everything(a, b, c, d, e, f, g, h,
					i, j, k, l, m);
		}
	}

	public static void Main(string[] args) {
		agnos.Servers.CmdlineServer server = new agnos.Servers.CmdlineServer(
				new FeatureTest.Processor(new Handler()));
		server.main(args);
	}

}
