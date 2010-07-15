using System;
using Agnos;
using FeatureTestBindings;
using System.Collections.Generic;


public class myserver 
{
	public class ClassA : FeatureTest.IClassA {
		private int val = 17;

		public int attr1 {
			get {
				return val;
			}
			set {
			}
		}

		public int attr2 {
			get {
				return 199;
			}
			set {
			}
		}

		// methods
		public int method1(string a, bool b)  {
			int v = b ? 7 : 3;
			return int.Parse(a) + v;
		}
	}
	
	public class ClassB : FeatureTest.IClassB {
		private int val = 17;
		private double val3 = 17.77;

		public int attr1 {
			get {
				return val;
			}
			set {
				val = value;
			}
		}

		public int attr2 {
			get {
				return 211;
			}
			set {
			}
		}

		public double attr3 {
			get {
				return val3;
			}
			set {
				val3 = value * 2;
			}
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
		private IList<FeatureTest.IClassA> _my_attr4;
		
		public ClassC(int a, int b, double c, IList<FeatureTest.IClassA> d)
		{
			val = a;
			val3 = c;
			_my_attr4 = d;
		}

		public int attr1 {
			get {
				return val;
			}
			set {
				val = value;
			}
		}

		public int attr2 {
			get {
				return 399;
			}
			set {
			}
		}

		public double attr3 {
			get {
				return val3;
			}
			set {
				val3 = value * 2;
			}
		}

		public IList<FeatureTest.IClassA> attr4 {
			get {
				return _my_attr4;
			}
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
		private string _name;
		private Person _father;
		private Person _mother;
		private Person _spouse;
		private DateTime _date_of_birth;
		private FeatureTest.Address _address;

		public Person(string name, FeatureTest.IPerson father,
				FeatureTest.IPerson mother) {
			this._name = name;
			this._father = (Person) father;
			this._mother = (Person) mother;
			this._address = new FeatureTest.Address(
					FeatureTest.State.TX, "nashville", "woldorf", 1772);
			this._date_of_birth = new DateTime();
		}

		// attributes
		public string name {
			get {
				return _name;
			}
		}

		public DateTime date_of_birth {
			get{
				return _date_of_birth;
			}
		}

		public FeatureTest.Address address {
			get{
				return _address;
			}
			set {
				_address = value;
			}
		}

		public FeatureTest.IPerson father  {
			get {
				return _father;
			}
		}

		public FeatureTest.IPerson mother  {
			get {
				return _mother;
			}
		}

		public FeatureTest.IPerson spouse {
			get{
				return _spouse;
			}
		}

		// methods
		public void marry(FeatureTest.IPerson partner)  {
			if (spouse != null) {
				throw new FeatureTest.MartialStatusError(
						"already married", this);
			}
			if (partner.spouse != null) {
				throw new FeatureTest.MartialStatusError(
						"already married", partner);
			}
			if ((mother != null && mother == partner.mother)
					|| (father != null && father == partner.father)) {
				throw new FeatureTest.MartialStatusError(
						"siblings cannot marry", partner);
			}
			_spouse = (Person) partner;
			_spouse._spouse = this;
		}

		public void divorce()  {
			if (spouse == null) {
				throw new FeatureTest.MartialStatusError(
						"does not have a spouse", this);
			}
			_spouse._spouse = null;
			_spouse = null;
		}

		public double think(double a, double b)  {
			return a / b;
		}
	}

	public class Handler : FeatureTest.IHandler {
		public FeatureTest.RecordB get_record_b()  
		{
			return new FeatureTest.RecordB(17, 18, 19);
		}

		public FeatureTest.IPerson Person_init(string name,
				FeatureTest.IPerson father,
				FeatureTest.IPerson mother)  
		{
			return new Person(name, father, mother);
		}

		public IList<FeatureTest.IClassC> get_class_c()  
		{
			List<FeatureTest.IClassA> x1 = new List<FeatureTest.IClassA>();
			x1.Add(new ClassA());
			x1.Add(new ClassA());
			List<FeatureTest.IClassA> x2 = new List<FeatureTest.IClassA>();
			x2.Add(new ClassA());

			List<FeatureTest.IClassC> arr = new List<FeatureTest.IClassC>();
			arr.Add(new ClassC(4, 5, 6.0, x1));
			arr.Add(new ClassC(33, 12, 76.2, x2));
			
			return arr;
		}

		public FeatureTest.Everything func_of_everything(Byte a,
				short b, int c, long d, double e, bool f, DateTime g,
				byte[] h, string i, IList<double> j, IDictionary<int, string> k,
				FeatureTest.Address l, FeatureTest.IPerson m)
				 {
			return new FeatureTest.Everything(a, b, c, d, e, f, g, h,
					i, j, k, l, m);
		}
	}

	public static void Main(string[] args) {
		Agnos.Servers.CmdlineServer server = new Agnos.Servers.CmdlineServer(
				new FeatureTest.Processor(new Handler()));
		server.Main(args);
	}

}
