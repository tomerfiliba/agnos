package agnos;

import java.io.*;
import java.util.*;
import java.net.*;
import java.util.concurrent.locks.*;

public class Transports 
{
	public interface ITransport
	{
		void close() throws IOException;
		InputStream getInputStream();
		OutputStream getOutputStream();

		// read interface
		int beginRead() throws IOException;
		int beginRead(int msecs) throws IOException;
		int read(byte[] data, int offset, int len) throws IOException;
		byte[] readAll() throws IOException;
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
		protected InputStream input;
		protected OutputStream output;
		protected ReentrantLock rlock;
		protected ReentrantLock wlock;
		protected InputStream asInputStream;
		protected OutputStream asOutputStream;

		protected int wseq;
		protected int rseq;
		protected int rpos;
		protected int rlength;

		public BaseTransport(InputStream input, OutputStream output)
		{
			this(input, output, 128 * 1024);
		}

		public BaseTransport(InputStream input, OutputStream output, int bufsize)
		{
			this.input = input;
			this.output = output;
			buffer = new ByteArrayOutputStream(bufsize);
			wlock = new ReentrantLock();
			rlock = new ReentrantLock();
			asInputStream = new TransportInputStream(this);
			asOutputStream = new TransportOutputStream(this);
		}
		
		public void close() throws IOException
		{
			// XXX: call endWrite here? 
			// then again, it might not make much sense
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
			if (rlock.isHeldByCurrentThread()) {
				throw new IOException("beginRead is not reentrant");
			}
			
			rlock.lock();
			rlength = (Integer)Packers.Int32.unpack(input);
			rseq = (Integer)Packers.Int32.unpack(input);
			rpos = 0;
			
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
			assertBeganRead();
			if (rpos + len > rlength) {
				throw new EOFException("request to read more than available");
			}
			int actually_read = input.read(data, offset, len);
			rpos += actually_read;
			return actually_read;
		}
		
		public byte[] readAll() throws IOException
		{
			byte[] data = new byte[rlength - rpos];
			read(data, 0, data.length);
			return data;
		}
		
		public synchronized void endRead() throws IOException
		{
			assertBeganRead();
			input.skip(rlength - rpos);
			rlock.unlock();
		}
		
		//
		// write interface
		//
		public synchronized void beginWrite(int seq) throws IOException
		{
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
			assertBeganWrite();
			buffer.write(data, offset, len);
		}
		
		public void reset() throws IOException
		{
			assertBeganWrite();
			buffer.reset();
		}

		public synchronized void endWrite() throws IOException
		{
			assertBeganWrite();
			if (buffer.size() > 0) {
				Packers.Int32.pack(buffer.size(), output);
				Packers.Int32.pack(wseq, output);
				buffer.writeTo(output);
				output.flush();
				buffer.reset();
			}
			wlock.unlock();
		}

		public synchronized void cancelWrite() throws IOException
		{
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
		public byte[] readAll() throws IOException {
			return transport.readAll();
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
		public SocketTransport(String host, int port) throws IOException
		{
			this(new Socket(host, port));
		}

		public SocketTransport(Socket sock) throws IOException
		{
			this(sock, 16 * 1024);
		}
		
		public SocketTransport(Socket sock, int bufsize) throws IOException
		{
			super(new BufferedInputStream(sock.getInputStream(), bufsize),
				new BufferedOutputStream(sock.getOutputStream(), bufsize));
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
				throws Exception {
			Process proc = procbuilder.start();
			BufferedReader reader = new BufferedReader(new InputStreamReader(
					new BufferedInputStream(proc.getInputStream())));
			String hostname = reader.readLine();
			int port = Integer.parseInt(reader.readLine());
			reader.close();

			return new ProcTransport(proc, new SocketTransport(hostname, port));
		}
	}

	public static class HttpClientTransport extends BaseTransport
	{
		public static final int ioBufferSize = 16 * 1024;
		
		protected URL url;
		
		public HttpClientTransport(String url) throws MalformedURLException
		{
			this(new URL(url));
		}

		public HttpClientTransport(URL url)
		{
			super(null, null);
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
				input = new BufferedInputStream(conn.getInputStream(), ioBufferSize);
			}
			wlock.unlock();
		}
	}

}
