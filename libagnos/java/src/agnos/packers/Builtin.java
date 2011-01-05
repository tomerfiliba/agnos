//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2011, International Business Machines Corp.
//                 Author: Tomer Filiba (tomerf@il.ibm.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//////////////////////////////////////////////////////////////////////////////

package agnos.packers;

import agnos.util._HeteroMapPacker;

public class Builtin {
	public static final int CUSTOM_PACKER_ID_BASE = 2000;

	public static final _Int8 Int8 = new _Int8();
	public static final _Bool Bool = new _Bool();
	public static final _Int16 Int16 = new _Int16();
	public static final _Int32 Int32 = new _Int32();
	public static final _Int64 Int64 = new _Int64();
	public static final _Float Float = new _Float();
	public static final _Buffer Buffer = new _Buffer();
	public static final _Date Date = new _Date();
	public static final _Str Str = new _Str();
	public static final _Null Null = new _Null();

	public static final ListOf<Byte> listOfInt8 = new ListOf<Byte>(800, Int8);
	public static final ListOf<Boolean> listOfBool = new ListOf<Boolean>(801,
			Bool);
	public static final ListOf<Short> listOfInt16 = new ListOf<Short>(802,
			Int16);
	public static final ListOf<Integer> listOfInt32 = new ListOf<Integer>(803,
			Int32);
	public static final ListOf<Long> listOfInt64 = new ListOf<Long>(804, Int64);
	public static final ListOf<Double> listOfFloat = new ListOf<Double>(805,
			Float);
	public static final ListOf<byte[]> listOfBuffer = new ListOf<byte[]>(806,
			Buffer);
	public static final ListOf<java.util.Date> listOfDate = new ListOf<java.util.Date>(807, Date);
	public static final ListOf<String> listOfStr = new ListOf<String>(808, Str);

	public static final SetOf<Byte> setOfInt8 = new SetOf<Byte>(820, Int8);
	public static final SetOf<Boolean> setOfBool = new SetOf<Boolean>(821, Bool);
	public static final SetOf<Short> setOfInt16 = new SetOf<Short>(822, Int16);
	public static final SetOf<Integer> setOfInt32 = new SetOf<Integer>(823,
			Int32);
	public static final SetOf<Long> setOfInt64 = new SetOf<Long>(824, Int64);
	public static final SetOf<Double> setOfFloat = new SetOf<Double>(825, Float);
	public static final SetOf<byte[]> setOfBuffer = new SetOf<byte[]>(826,
			Buffer);
	public static final SetOf<java.util.Date> setOfDate = new SetOf<java.util.Date>(827, Date);
	public static final SetOf<String> setOfStr = new SetOf<String>(828, Str);

	public static final MapOf<Integer, Integer> mapOfInt32Int32 = new MapOf<Integer, Integer>(
			850, Int32, Int32);
	public static final MapOf<Integer, String> mapOfInt32Str = new MapOf<Integer, String>(
			851, Int32, Str);
	public static final MapOf<String, Integer> mapOfStrInt32 = new MapOf<String, Integer>(
			852, Str, Int32);
	public static final MapOf<String, String> mapOfStrStr = new MapOf<String, String>(
			853, Str, Str);

	public static final _HeteroMapPacker heteroMapPacker = new _HeteroMapPacker(
			998, null);
}
