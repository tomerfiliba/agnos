// ////////////////////////////////////////////////////////////////////////////
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
// ////////////////////////////////////////////////////////////////////////////

package agnos.transportFactories;

import java.io.Closeable;
import java.io.IOException;
import agnos.transports.ITransport;

/**
 * Defines the required methods of a transport factory 
 * 
 * @author Tomer Filiba
 */
public interface ITransportFactory extends Closeable {
	/**
	 * closes the transport factory and releases all related system resources
	 */
	void close() throws IOException;

	/**
	 * accepts a new transport. this method will block until a new connection
	 * arrives.
	 * 
	 * @return the newly accepted Transport instance
	 */
	ITransport accept() throws IOException;
}
