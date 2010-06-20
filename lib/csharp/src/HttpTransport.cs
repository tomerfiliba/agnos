using System;
using System.IO;
using System.Net;
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;


namespace Agnos.Transports
{
	public class HttpClientTransport : Stream, ITransport
	{
		Uri uri;
		WebResponse resp;
		MemoryStream mstream;
		
		public ICredentials Credentials = null;
		public bool PreAuthenticate = false;
		public bool AllowAutoRedirect = true;
		public int TimeoutMsec = 120000; // 2 minutes
		public IWebProxy Proxy = null;
		public AuthenticationLevel AuthenticationLevel = AuthenticationLevel.None;
		public X509CertificateCollection ClientCertificates;
		// CookieContainer ?

		public HttpClientTransport (Uri uri)
		{
			this.uri = uri;
			resp = null;
			mstream = new MemoryStream(128 * 1024);
		}
		
		public Stream getInputStream()
		{
			return this;
		}
		public Stream getOutputStream()
		{
			return this;
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

		public override void Close()
		{
			Flush();
		}

		public override void Flush ()
		{
			byte[] data = mstream.GetBuffer();
			
			if (data.Length <= 0) {
				return;
			}
			
			WebRequest req = buildRequest();
			
            req.ContentLength = data.Length;
            using (Stream s = req.GetRequestStream()) {
                s.Write(data, 0, data.Length);
            }
			mstream.Position = 0;
			mstream.SetLength(0);
			
			resp = req.GetResponse();
		}
		
		public override int Read (byte[] buffer, int offset, int count)
		{
			if (resp == null) {
				throw new InvalidOperationException("cannot read before flush()ing");
			}
			Stream respStream = resp.GetResponseStream();
			return respStream.Read(buffer, offset, count);
		}
		
		public override void Write (byte[] buffer, int offset, int count)
		{
			resp = null;
			mstream.Write(buffer, offset, count);
		}
		
		public override bool CanRead
		{
			get{
				return true;
			}
		}
		public override bool CanSeek {
			get {
				return false;
			}
		}
		public override bool CanWrite {
			get {
				return true;
			}
		}
		public override long Length {
			get {
				throw new InvalidOperationException();
			}
		}
		public override long Position {
			get {
				throw new InvalidOperationException();
			}
			set {
				throw new InvalidOperationException();
			}
		}
		public override long Seek (long offset, SeekOrigin origin)
		{
			throw new InvalidOperationException();
		}
		public override void SetLength (long value)
		{
			throw new InvalidOperationException();
		}




			
	}
}


