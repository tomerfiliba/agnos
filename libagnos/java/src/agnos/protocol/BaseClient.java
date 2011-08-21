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

import java.io.IOException;
import java.io.Closeable;

import agnos.util.HeteroMap;

public class BaseClient implements Closeable
{
	public ClientUtils _utils;
	
	public void close() throws IOException
	{
		_utils.close();
	}

	public HeteroMap getServiceInfo(int code) throws IOException,
			ProtocolException, PackedException, GenericException
	{
		return _utils.getServiceInfo(code);
	}
}
