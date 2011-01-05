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

import java.io.IOException;
import java.net.InetAddress;

import javax.net.ssl.SSLServerSocket;
import javax.net.ssl.SSLServerSocketFactory;


/**
 * An SSL-enabled version of SocketTransportFactory
 * 
 * @author Tomer Filiba
 */
public class SSLSocketTransportFactory extends SocketTransportFactory {
	/**
	 * Constructs a TCP SSLSocketTransportFactory listening on the localhost at
	 * the given port with the default backlog and default
	 * SSLServerSocketFactory
	 */
	public SSLSocketTransportFactory(int port) throws IOException {
		this(port, DEFAULT_BACKLOG);
	}

	/**
	 * Constructs a TCP SSLSocketTransportFactory listening on the localhost at
	 * the given port with the given backlog and default SSLServerSocketFactory
	 */
	public SSLSocketTransportFactory(int port, int backlog) throws IOException {
		this(InetAddress.getLocalHost(), port, backlog);
	}

	/**
	 * Constructs a TCP SSLSocketTransportFactory listening on the given host at
	 * the given port with the default backlog and default
	 * SSLServerSocketFactory
	 */
	public SSLSocketTransportFactory(String host, int port) throws IOException {
		this(host, port, DEFAULT_BACKLOG);
	}

	/**
	 * Constructs a TCP SSLSocketTransportFactory listening on the given host at
	 * the given port with the given backlog and default SSLServerSocketFactory
	 */
	public SSLSocketTransportFactory(String host, int port, int backlog)
			throws IOException {
		this((SSLServerSocketFactory) SSLServerSocketFactory.getDefault(),
				InetAddress.getByName(host), port, backlog);
	}

	/**
	 * Constructs a TCP SSLSocketTransportFactory listening on the given
	 * InetAddress at the given port with the given backlog and default
	 * SSLServerSocketFactory
	 */
	public SSLSocketTransportFactory(InetAddress addr, int port, int backlog)
			throws IOException {
		this((SSLServerSocketFactory) SSLServerSocketFactory.getDefault(),
				addr, port, backlog);
	}

	/**
	 * Constructs a TCP SSLSocketTransportFactory listening on the given
	 * InetAddress at the given port with the given backlog, using the given
	 * SSLServerSocketFactory
	 */
	public SSLSocketTransportFactory(SSLServerSocketFactory factory,
			InetAddress addr, int port, int backlog) throws IOException {
		this((SSLServerSocket) factory.createServerSocket(port, backlog, addr));
	}

	/**
	 * Constructs a SSLSocketTransportFactory from the given pre-configured 
	 * SSLServerSocket instance
	 */
	public SSLSocketTransportFactory(SSLServerSocket serverSocket) {
		super(serverSocket);
	}
}
