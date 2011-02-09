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

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * An adapter class that allows chaining of transports: all transport
 * operations are carried out on the inner transport object.
 * 
 * @author Tomer Filiba
 *
 */
public abstract class WrappedTransport implements ITransport
{
	protected ITransport transport;

	public WrappedTransport(ITransport transport)
	{
		this.transport = transport;
	}

	@Override
	public InputStream getInputStream()
	{
		return transport.getInputStream();
	}

	@Override
	public OutputStream getOutputStream()
	{
		return transport.getOutputStream();
	}

	@Override
	public bool isCompressionEnabled()
	{
		return transport.isCompressionEnabled();
	}
	
	@Override
	public void enableCompression()
	{
		transport.enableCompression();
	}

	@Override
	public void disableCompression() 
	{
		transport.disableCompression();
	}
	
	@Override
	public void close() throws IOException
	{
		transport.close();
	}

	@Override
	public int beginRead() throws IOException
	{
		return transport.beginRead();
	}

	@Override
	public int beginRead(int msecs) throws IOException
	{
		return transport.beginRead(msecs);
	}

	@Override
	public int read(byte[] data, int offset, int len) throws IOException
	{
		return transport.read(data, offset, len);
	}

	@Override
	public void endRead() throws IOException
	{
		transport.endRead();
	}

	@Override
	public void beginWrite(int seq) throws IOException
	{
		transport.beginWrite(seq);
	}

	@Override
	public void write(byte[] data, int offset, int len) throws IOException
	{
		transport.write(data, offset, len);
	}

	@Override
	public void restartWrite() throws IOException
	{
		transport.restartWrite();
	}

	@Override
	public void endWrite() throws IOException
	{
		transport.endWrite();
	}

	@Override
	public void cancelWrite() throws IOException
	{
		transport.cancelWrite();
	}
}
