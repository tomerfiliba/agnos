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

using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Net.Security;
using System.Security.Authentication;
using System.Security.Cryptography.X509Certificates;
using Agnos.Transports;


namespace Agnos.TransportFactories
{
	/// <summary>
	/// a factory class for transports
	/// </summary>
	public interface ITransportFactory
	{
		/// <summary>
		/// waits (blocking) for an incoming connection and returns it as an
		/// instance of ITransport
		/// </summary>
		/// <returns>
		/// A <see cref="ITransport"/>
		/// </returns>
		ITransport Accept();
		
		/// <summary>
		/// Closes the transport factory and releases all associated system
		/// resources (e.g., the listener socket, etc.)
		/// </summary>
		void Close();
	}


	/// <summary>
	/// A TransportFactory that waits for incoming TCP connections and 
	/// returns SocketTransport instances
	/// </summary>
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

		virtual public ITransport Accept()
		{
			return new SocketTransport(listener.AcceptSocket());
		}
		
		public void Close()
		{
			listener.Stop();
		}
	}
	
	/// <summary>
	/// SSL-enabled version of SocketTransportFactory
	/// </summary>
	public class SslSocketTransportFactory : SocketTransportFactory
	{
		RemoteCertificateValidationCallback certificateValidationCallback;
		LocalCertificateSelectionCallback certificateSelectionCallback;
		//EncryptionPolicy encryptionPolicy;
		//
		protected X509Certificate serverCertificate;
		protected bool clientCertificateRequired;
		protected SslProtocols enabledSslProtocols;
		protected bool checkCertificateRevocation; 


		public SslSocketTransportFactory(
				String host,
				int port,
				X509Certificate serverCertificate) :
			this(GetIPv4AddressOf(host), port, DefaultBacklog,
				null, null, //EncryptionPolicy.NoEncryption,
				serverCertificate, false, SslProtocols.Default, false)
		{
		}
		
		public SslSocketTransportFactory(
				IPAddress addr,
				int port,
				int backlog,
				//
				RemoteCertificateValidationCallback certificateValidationCallback,
				LocalCertificateSelectionCallback certificateSelectionCallback,
				//EncryptionPolicy encryptionPolicy,
				//
				X509Certificate serverCertificate,
				bool clientCertificateRequired,
				SslProtocols enabledSslProtocols,
				bool checkCertificateRevocation) : 
			base(addr, port, backlog)
		{
			this.certificateValidationCallback = certificateValidationCallback;
			this.certificateSelectionCallback = certificateSelectionCallback;
			//this.encryptionPolicy = encryptionPolicy;
			//
			this.serverCertificate = serverCertificate;
			this.clientCertificateRequired = clientCertificateRequired;
			this.enabledSslProtocols = enabledSslProtocols;
			this.checkCertificateRevocation = checkCertificateRevocation;
		}

		override public ITransport Accept()
		{
			Socket sock2 = listener.AcceptSocket();
			SslStream ssl = new SslStream(new NetworkStream(sock2, true), 
				false, certificateValidationCallback, certificateSelectionCallback);
			ssl.AuthenticateAsServer(serverCertificate, clientCertificateRequired, 
				enabledSslProtocols, checkCertificateRevocation);
			return new SslSocketTransport(ssl);
		}
	}
	
}