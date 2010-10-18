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
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;


namespace Agnos.Transports
{
    public class HttpClientTransport : BaseTransport
    {
        public const int ioBufferSize = 16 * 1024;
        protected Uri uri;
        protected WebResponse resp;

        public ICredentials Credentials = null;
        public bool PreAuthenticate = false;
        public bool AllowAutoRedirect = true;
        public int TimeoutMsec = 120000; // 2 minutes
        public IWebProxy Proxy = null;
        public AuthenticationLevel AuthenticationLevel = AuthenticationLevel.None;
        public X509CertificateCollection ClientCertificates;

        public HttpClientTransport(String uri)
            : this(new Uri(uri))
        {
        }

        public HttpClientTransport(Uri uri)
            : base(null, null)
        {
            this.uri = uri;
        }

        protected HttpWebRequest buildRequest()
        {
            HttpWebRequest req = (HttpWebRequest)WebRequest.Create(uri);

            req.Credentials = Credentials;
            req.PreAuthenticate = PreAuthenticate;
            req.Method = "POST";
            req.ContentType = "application/octet-stream";
            req.AutomaticDecompression = DecompressionMethods.Deflate | DecompressionMethods.GZip | DecompressionMethods.None;
            req.AuthenticationLevel = AuthenticationLevel;
            req.AllowAutoRedirect = AllowAutoRedirect;
            req.Proxy = Proxy;
            req.ClientCertificates = ClientCertificates;
            //req.CachePolicy = 

            return req;
        }

		public override int BeginRead()
		{
			return BeginRead(-1);
		}

		public override int BeginRead(int msecs)
		{
			if (inputStream == null) {
				throw new IOException("BeginRead must be called only after EndWrite");
			}
			return base.BeginRead(msecs);
		}
		
        public override void EndRead()
        {
            lock (this)
            {
                AssertBeganRead();
                inputStream.Close();
                inputStream = null;
				resp = null;
                rlock.Release();
            }
        }

        public override void EndWrite()
        {
            lock (this)
            {
                AssertBeganWrite();
                if (buffer.Length > 0)
                {
                    WebRequest req = buildRequest();
                    req.ContentLength = buffer.Length + 8;
                    
                    outputStream = req.GetRequestStream();
                    Packers.Int32.pack((int)buffer.Length, outputStream);
                    Packers.Int32.pack(wseq, outputStream);
                    buffer.WriteTo(outputStream);
                    outputStream.Flush();
                    buffer.Position = 0;
                    buffer.SetLength(0);
                    outputStream.Close();
                    outputStream = null;

                    if (inputStream != null)
                    {
                        inputStream.Close();
                    }
                    resp = req.GetResponse();
                    inputStream = new BufferedStream(resp.GetResponseStream(), ioBufferSize);
                }
                wlock.Release();
            }
        }

    }

}


