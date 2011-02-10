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
			if (inStream == null) {
				throw new IOException("BeginRead must be called only after EndWrite");
			}
			return base.BeginRead();
		}
		
        public override void EndRead()
        {
            AssertBeganRead();
            inStream.Close();
            inStream = null;
            readStream = null;
			resp = null;
            rlock.Release();
        }

        public override void EndWrite()
        {
            AssertBeganWrite();
            if (wbuffer.Length > 0)
            {
                WebRequest req = buildRequest();
                req.ContentLength = wbuffer.Length + 12;
                
                outStream = req.GetRequestStream();
                writeSInt32(outStream, wseq);
                writeSInt32(outStream, (int)wbuffer.Length);
                writeSInt32(outStream, 0);
                wbuffer.WriteTo(outStream);
                outStream.Flush();
                wbuffer.Position = 0;
                wbuffer.SetLength(0);
                outStream.Close();
                outStream = null;

                if (inStream != null) {
                    inStream.Close();
                }
                resp = req.GetResponse();
                inStream = new BufferedStream(resp.GetResponseStream(), ioBufferSize);
            }
            wlock.Release();
        }

    }

}


