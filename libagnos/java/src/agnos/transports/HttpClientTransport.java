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

package agnos.transports;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;

import agnos.packers.Builtin;



/**
 * An HTTP-based client transport. Instead of operating over a direct socket,
 * this kind of transport allows you to connect to an HTTP server that would
 * relay the protocol's payload to an Agnos server behind the scenes. This
 * is useful when you have to "integrate" with an HTTP server in your setup. 
 * 
 * @author Tomer Filiba
 *
 */
public class HttpClientTransport extends BaseTransport
{
	protected URL url;

	/**
	 * Constructs an HttpClientTransport from a URL (given as a string)
	 */
	public HttpClientTransport(String url) throws MalformedURLException
	{
		this(new URL(url));
	}

	/**
	 * Constructs an HttpClientTransport from a URL (given as a URL object)
	 */
	public HttpClientTransport(URL url)
	{
		super(null, null);
		this.url = url;
	}

	@Override
	protected int getCompressionThreshold() {
		return 4 * 1024;
	}

	/**
	 * helper method that constructs an HttpURLConnection
	 */
	/*protected HttpURLConnection buildConnection() throws IOException
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
	}*/

	/*@Override
	public int beginRead() throws IOException
	{
		if (input == null) {
			throw new IOException(
					"beginRead must be called only after endWrite");
		}
		return super.beginRead();
	}*/

	/*@Override
	public synchronized void endRead() throws IOException
	{
		assertBeganRead();
		input.close();
		input = null;
		rlock.unlock();
	}*/

	/*@Override
	public synchronized void endWrite() throws IOException
	{
		//
		// TODO: missing compression support!
		//
		assertBeganWrite();
		if (buffer.size() > 0) {
			URLConnection conn = buildConnection();

			output = conn.getOutputStream();
			Builtin.Int32.pack(buffer.size(), output);
			Builtin.Int32.pack(wseq, output);
			buffer.writeTo(output);
			output.flush();
			buffer.reset();
			output.close();
			output = null;

			if (input != null) {
				input.close();
			}
			input = new BufferedInputStream(conn.getInputStream(),
					DEFAULT_IO_SIZE);
		}
		wlock.unlock();
	}*/
}
