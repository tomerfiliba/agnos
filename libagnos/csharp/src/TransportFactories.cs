//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2010, Tomer Filiba (tomerf@il.ibm.com; tomerfiliba@gmail.com)
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

using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using Agnos.Transports;


namespace Agnos.TransportFactories
{
	public interface ITransportFactory
	{
		Transports.ITransport Accept();
		void Close();
	}

	public class SocketTransportFactory : ITransportFactory
	{
		internal TcpListener listener;
        public const int DefaultBacklog = 10;

		public SocketTransportFactory(int port) :
			this(IPAddress.Any, port)
		{
		}

		public SocketTransportFactory(int port, int backlog) :
			this(IPAddress.Any, port, backlog)
		{
		}

        protected static IPAddress GetIPv4AddressOf(String host)
        {
            foreach (IPAddress addr in Dns.GetHostEntry(host).AddressList) {
                if (addr.AddressFamily == AddressFamily.InterNetwork) {
                    return addr;
                }
            }
            return null;
        }

		public SocketTransportFactory(String host, int port) :
            this(GetIPv4AddressOf(host), port)
		{
		}

		public SocketTransportFactory(String host, int port, int backlog) :
            this(GetIPv4AddressOf(host), port, backlog)
		{
		}

        public SocketTransportFactory(IPAddress addr, int port) :
            this(addr, port, DefaultBacklog)
        {
        }

        public SocketTransportFactory(IPAddress addr, int port, int backlog)
        {
            listener = new TcpListener(addr, port);
            listener.Start(backlog);
        }

		public ITransport Accept()
		{
			return new SocketTransport(listener.AcceptSocket());
		}
		
		public void Close()
		{
			listener.Stop();
		}
	}
	
}