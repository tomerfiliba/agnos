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

package agnos.protocol;


public class constants
{
	public static final byte CMD_PING = 0;
	public static final byte CMD_INVOKE = 1;
	public static final byte CMD_QUIT = 2;
	public static final byte CMD_DECREF = 3;
	public static final byte CMD_INCREF = 4;
	public static final byte CMD_GETINFO = 5;
	public static final byte CMD_CHECK_CAST = 6;
	public static final byte CMD_QUERY_PROXY_TYPE = 7;

	public static final byte REPLY_SUCCESS = 0;
	public static final byte REPLY_PROTOCOL_EXCEPTION = 1;
	public static final byte REPLY_PACKED_EXCEPTION = 2;
	public static final byte REPLY_GENERIC_EXCEPTION = 3;

	public static final int INFO_META = 0;
	public static final int INFO_SERVICE = 1;
	public static final int INFO_FUNCTIONS = 2;
	public static final int INFO_REFLECTION = 3;
	
	private constants() {
	}
}
