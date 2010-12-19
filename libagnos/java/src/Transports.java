//////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
//    http://agnos.sourceforge.net
//
// Copyright 2010, International Business Machines Corp.
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

package agnos;

import java.io.*;
import java.util.*;
import java.util.zip.*;

import java.net.*;
import javax.net.ssl.*;
import java.util.concurrent.locks.*;


public class Transports 
{
	/*protected static String repr(byte[] arr, int off, int len)
	{
		StringBuffer sb = new StringBuffer(len*2);
		int end = Math.min(arr.length, off+len);
		for (int i = off; i < end; i++) {
			if (arr[i] < 32 || arr[i] > 126) {
				sb.append(String.format("\\x%02x", arr[i])); 
			}
			else {
				sb.append((char)(arr[i]));
			}
		}
		return sb.toString();
	}
	
	protected static String repr(byte[] arr)
	{
		return repr(arr, 0, arr.length);
	}*/
	
	public static class TransportException extends IOException
	{
		public TransportException(String message)
		{
			super(message);
		}
	}	
	
	public interface ITransport
	{
		void close() throws IOException;
		InputStream getInputStream();
		OutputStream getOutputStream();

		// read interface
		int beginRead() throws IOException;
		int beginRead(int msecs) throws IOException;
		int read(byte[] data, int offset, int len) throws IOException;
		void endRead() throws IOException;
		
		// write interface
		void beginWrite(int seq) throws IOException;
		void write(byte[] data, int offset, int len) throws IOException;
		void reset() throws IOException;
		void endWrite() throws IOException;
		void cancelWrite() throws IOException;
	}

	protected static class TransportInputStream extends InputStream
	{
		ITransport transport;
		public TransportInputStream(ITransport transport)
		{
			this.transport = transport;
		}
		public int read() throws IOException
		{
			byte[] buffer = {0};
			read(buffer);
			return buffer[0];
		}
		public int read(byte[] data, int off, int len) throws IOException
		{
			return transport.read(data, off, len);
		}
	}

	protected static class TransportOutputStream extends OutputStream
	{
		ITransport transport;
		public TransportOutputStream(ITransport transport)
		{
			this.transport = transport;
		}
		public void write(int b) throws IOException
		{
			byte[] buffer = {(byte)b};
			write(buffer);
		}
		public void write(byte[] data, int off, int len) throws IOException
		{
			transport.write(data, off, len);
		}
	}
	
	public static abstract class BaseTransport implements ITransport
	{
		protected ByteArrayOutputStream buffer;
		protected ByteArrayOutputStream buffer2;
		protected InputStream input;
		protected InputStream input2;
		protected OutputStream output;
		protected ReentrantLock rlock;
		protected ReentrantLock wlock;
		protected InputStream asInputStream;
		protected OutputStream asOutputStream;

		protected int wseq;
		protected int rseq;
		protected int rpos;
		protected int rlength;
		protected int rcomplength;

		// to disable compression, set to a negative number
		protected int compressionThreshold;

		public static final int DEFAULT_BUFFER_SIZE = 128 * 1024;
		
		public BaseTransport(InputStream input, OutputStream output, 
				int compressionThreshold)
		{
			this.input = input;
			this.output = output;
			this.compressionThreshold = -1; // compressionThreshold;
			input2 = null;
			buffer = new ByteArrayOutputStream(DEFAULT_BUFFER_SIZE);
			buffer2 = new ByteArrayOutputStream(DEFAULT_BUFFER_SIZE);
			wlock = new ReentrantLock();
			rlock = new ReentrantLock();
			asInputStream = new TransportInputStream(this);
			asOutputStream = new TransportOutputStream(this);
		}
		
		public void close() throws IOException
		{
			//System.out.printf("[%s.close]\n", this);
			if (input != null) {
				input.close();
				input = null;
			}
			if (output != null) {
				output.close();
				output = null;
			}
		}

		public InputStream getInputStream()
		{
			return asInputStream;
		}

		public OutputStream getOutputStream()
		{
			return asOutputStream;
		}
		
		//
		// read interface
		//
		public synchronized int beginRead() throws IOException
		{
			return beginRead(-1);
		}
		
		public synchronized int beginRead(int msecs) throws IOException
		{
			//System.out.printf("[%s.beginRead] ", this);
			if (rlock.isHeldByCurrentThread()) {
				throw new IOException("beginRead is not reentrant");
			}
			
			rlock.lock();
			rseq = (Integer)Packers.Int32.unpack(input);
			rlength = (Integer)Packers.Int32.unpack(input);
			rcomplength = (Integer)Packers.Int32.unpack(input);
			rpos = 0;
			//System.out.printf("length = %d, seq = %d, compressed = %s\n", 
			//		rlength, rseq, (rcomplength > 0) ? "T" : "F");
			
			//if (rcomplength > 0) {
			//	input2 = new InflaterInputStream(input);
			//	int tmp = rlength;
			//	rlength = rcomplength;
			//	rcomplength = tmp;
			//}
			//else {
			input2 = input;
			//}
			
			return rseq;
		}

		protected void assertBeganRead() throws IOException
		{
			if (!rlock.isHeldByCurrentThread()) {
				throw new IOException("thread must first call beginRead");
			}
		}
		
		public int read(byte[] data, int offset, int len) throws IOException
		{
			//System.out.printf("[%s.read(%d)] ", this, len);
			assertBeganRead();
			if (rpos + len > rlength) {
				throw new EOFException("request to read more than available");
			}
			int actually_read = input2.read(data, offset, len);
			//System.out.printf("%s\n", repr(data, offset, len));
			rpos += actually_read;
			return actually_read;
		}
		
		public synchronized void endRead() throws IOException
		{
			//System.out.printf("[%s.endRead()]\n", this);
			assertBeganRead();
			input2.skip(rlength - rpos);
			rlock.unlock();
			input2 = null;
		}
		
		//
		// write interface
		//
		public synchronized void beginWrite(int seq) throws IOException
		{
			//System.out.printf("[%s.beginWrite(%d)]\n", this, seq);
			if (wlock.isHeldByCurrentThread()) {
				throw new IOException("beginWrite is not reentrant");
			}
			wlock.lock();
			wseq = seq;
			buffer.reset();
		}
		
		protected void assertBeganWrite() throws IOException
		{
			if (!wlock.isHeldByCurrentThread()) {
				throw new IOException("thread must first call beginWrite");
			}
		}

		public void write(byte[] data, int offset, int len) throws IOException
		{
			//System.out.printf("[%s.write(%d)] %s\n", this, len, 
			//		repr(data, offset, len));
			assertBeganWrite();
			buffer.write(data, offset, len);
		}
		
		public void reset() throws IOException
		{
			//System.out.printf("[%s.reset()]\n", this);
			assertBeganWrite();
			buffer.reset();
		}

		public synchronized void endWrite() throws IOException
		{
			int len = buffer.size();
			//System.out.printf("[%s.endWrite(%d)] ", this, len);
			assertBeganWrite();
			
			if (len > 0) {
				Packers.Int32.pack(wseq, output);
				
				if (compressionThreshold >= 0 && len > compressionThreshold) {
					buffer2.reset();
					DeflaterOutputStream comp = new DeflaterOutputStream(buffer2);
					buffer.writeTo(comp);
					comp.finish();
					
					//System.out.printf("compressed to %d\n", buffer2.size());
					Packers.Int32.pack(buffer2.size(), output); // actual size
					Packers.Int32.pack(len, output); // uncompressed size
					buffer2.writeTo(output);
				}
				else {
					//System.out.printf("uncompressed\n");
					
					Packers.Int32.pack(len, output); // actual size
					Packers.Int32.pack(0, output); // 0 means no compression
					buffer.writeTo(output);
				}
				
				output.flush();
				buffer.reset();
			}
			wlock.unlock();
		}

		public synchronized void cancelWrite() throws IOException
		{
			//System.out.printf("[%s.cancelWrite()]\n", this);
			assertBeganWrite();
			buffer.reset();
			wlock.unlock();
		}
	}
	

	public static abstract class WrappedTransport implements ITransport
	{
		protected ITransport transport;
		
		public WrappedTransport(ITransport transport) {
			this.transport = transport;
		}
		public InputStream getInputStream() {
			return transport.getInputStream();
		}
		public OutputStream getOutputStream() {
			return transport.getOutputStream();
		}
		public void close() throws IOException {
			transport.close();
		}
		public int beginRead() throws IOException {
			return transport.beginRead();
		}
		public int beginRead(int msecs) throws IOException {
			return transport.beginRead(msecs);
		}
		public int read(byte[] data, int offset, int len) throws IOException {
			return transport.read(data, offset, len);
		}
		public void endRead() throws IOException {
			transport.endRead();
		}
		public void beginWrite(int seq) throws IOException {
			transport.beginWrite(seq);
		}
		public void write(byte[] data, int offset, int len) throws IOException {
			transport.write(data, offset, len);
		}
		public void reset() throws IOException {
			transport.reset();
		}
		public void endWrite() throws IOException {
			transport.endWrite();
		}
		public void cancelWrite() throws IOException {
			transport.cancelWrite();
		}
	}
	
	
	public static class SocketTransport extends BaseTransport
	{
		public static final int DEFAULT_BUFFER_SIZE = 32 * 1024;
		public static final int DEFAULT_COMPRESSION_THRESHOLD = 4 * 1024;
		
		
		public SocketTransport(String host, int port) throws IOException
		{
			this(host, port, DEFAULT_BUFFER_SIZE, DEFAULT_COMPRESSION_THRESHOLD);
		}

		public SocketTransport(String host, int port, int bufsize, int compressionThreshold) throws IOException
		{
			this(new Socket(host, port), bufsize, compressionThreshold);
		}

		public SocketTransport(Socket sock) throws IOException
		{
			this(sock, DEFAULT_BUFFER_SIZE, DEFAULT_COMPRESSION_THRESHOLD);
		}

		public SocketTransport(Socket sock, int bufsize, int compressionThreshold) throws IOException
		{
			super(new BufferedInputStream(sock.getInputStream(), bufsize),
				new BufferedOutputStream(sock.getOutputStream(), bufsize),
				compressionThreshold);
		}
	}

	
	public static class SSLSocketTransport extends SocketTransport
	{
		public SSLSocketTransport(String host, int port) throws IOException
		{
			this(host, port, DEFAULT_BUFFER_SIZE, DEFAULT_COMPRESSION_THRESHOLD);
		}

		public SSLSocketTransport(String host, int port, int bufsize, int compressionThreshold) throws IOException
		{
			this((SSLSocket)(SSLSocketFactory.getDefault().createSocket(host, port)),
					bufsize, compressionThreshold);
		}

		public SSLSocketTransport(SSLSocket sock) throws IOException
		{
			this(sock, DEFAULT_BUFFER_SIZE, DEFAULT_COMPRESSION_THRESHOLD);
		}

		public SSLSocketTransport(SSLSocket sock, int bufsize, int compressionThreshold) throws IOException
		{
			super(sock, bufsize, compressionThreshold);
		}
	}
	
	
	public static class ProcTransport extends WrappedTransport 
	{
		public Process proc;
		
		public ProcTransport(Process proc, ITransport transport) {
			super(transport);
			this.proc = proc;
		}

		public static ProcTransport connect(String filename) throws Exception {
			return connect(filename, "-m", "lib");
		}

		public static ProcTransport connect(String filename, String... args)
				throws Exception {
			ArrayList<String> cmdline = new ArrayList<String>();
			cmdline.add(filename);
			cmdline.addAll(Arrays.asList(args));
			ProcessBuilder pb = new ProcessBuilder(cmdline);
			pb.redirectErrorStream(true);
			return connect(pb);
		}

		public static ProcTransport connect(ProcessBuilder procbuilder)
				throws Exception 
		{
			Process proc = procbuilder.start();
			BufferedReader stdout = new BufferedReader(new InputStreamReader(
					new BufferedInputStream(proc.getInputStream())));
			BufferedReader stderr = new BufferedReader(new InputStreamReader(
					new BufferedInputStream(proc.getErrorStream())));
			
			String banner = stdout.readLine();
			
			if (banner == null || !banner.equals("AGNOS")) {
				StringBuilder sb = new StringBuilder(4000);
				
				sb.append("Process " + proc + " either failed to start or is not an Agnos server");
				sb.append("\nStdout:\n");
				if (banner != null) {
					sb.append("|    " + banner + "\n");
				}
				while (true) {
					String line = stdout.readLine();
					if (line == null) {
						break;
					}
					sb.append("|    " + line + "\n");
				}
				
				sb.append("Stderr:\n");
				while (true) {
					String line = stderr.readLine();
					if (line == null) {
						break;
					}
					sb.append("|    " + line + "\n");
				}
				
				proc.destroy();
				
				throw new TransportException(sb.toString());
			}
			
			String hostname = stdout.readLine();
			int port = Integer.parseInt(stdout.readLine());
			stdout.close();
			stderr.close();

			return new ProcTransport(proc, 
					new SocketTransport(hostname, port, 
							SocketTransport.DEFAULT_BUFFER_SIZE, -1));
		}
	}
	

	public static class HttpClientTransport extends BaseTransport
	{
		public static final int DEFAULT_IO_SIZE = 32 * 1024;
		public static final int DEFAULT_COMPRESSION_THRESHOLD = 4 * 1024;
		
		protected URL url;
		
		public HttpClientTransport(String url) throws MalformedURLException
		{
			this(new URL(url));
		}

		public HttpClientTransport(URL url)
		{
			this(url, DEFAULT_COMPRESSION_THRESHOLD);
		}

		public HttpClientTransport(URL url, int compressionThreshold)
		{
			super(null, null, compressionThreshold);
			this.url = url;
		}

		protected HttpURLConnection buildConnection() throws IOException 
		{
			HttpURLConnection conn = (HttpURLConnection) url.openConnection();

			conn.setDoOutput(true);
			conn.setAllowUserInteraction(false);
			conn.setUseCaches(false);
			conn.setInstanceFollowRedirects(true);
			conn.setRequestMethod("POST");
			conn.setRequestProperty("content-type", "application/octet-stream");
			conn.connect();
			return conn;
		}

		public int beginRead() throws IOException
		{
			return beginRead(-1);
		}

		public int beginRead(int msecs) throws IOException
		{
			if (input == null) {
				throw new IOException("beginRead must be called only after endWrite");
			}
			return super.beginRead(msecs);
		}
		
		public synchronized void endRead() throws IOException
		{
			assertBeganRead();
			input.close();
			input = null;
			rlock.unlock();
		}
		
		public synchronized void endWrite() throws IOException 
		{
			assertBeganWrite();
			if (buffer.size() > 0) {
				URLConnection conn = buildConnection();
				
				output = conn.getOutputStream();
				Packers.Int32.pack(buffer.size(), output);
				Packers.Int32.pack(wseq, output);
				buffer.writeTo(output);
				output.flush();
				buffer.reset();
				output.close();
				output = null;
				
				if (input != null) {
					input.close();
				}
				input = new BufferedInputStream(conn.getInputStream(), DEFAULT_IO_SIZE);
			}
			wlock.unlock();
		}
	}

}
