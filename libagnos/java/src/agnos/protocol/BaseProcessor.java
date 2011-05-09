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

package agnos.protocol;

import java.io.IOException;
import java.io.Closeable;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.HashMap;
import java.util.Map;

import agnos.packers.Builtin;
import agnos.packers.ISerializer;
import agnos.transports.ITransport;
import agnos.util.HeteroMap;
import agnos.util.ObjectIDGenerator;

public abstract class BaseProcessor implements ISerializer, Closeable {
	protected static final class Cell {
		public int refcount;
		public final Object obj;

		public Cell(Object obj) {
			refcount = 1;
			this.obj = obj;
		}

		public void incref() {
			refcount += 1;
		}

		public boolean decref() {
			refcount -= 1;
			return refcount <= 0;
		}
	}

	protected abstract static class FunctionHandler
	{
		abstract public Object[] parseArgs(ITransport transport) throws Exception;
		abstract public void invoke(ITransport transport, Object[] args) throws Exception;
	}

	protected Map<Long, Cell> cells;
	protected Map<Integer, FunctionHandler> funcHandlers;
	protected ObjectIDGenerator idGenerator;
	protected ITransport transport;

	public BaseProcessor(ITransport transport) {
		cells = new HashMap<Long, Cell>();
		idGenerator = new ObjectIDGenerator();
		this.transport = transport;
		funcHandlers = new HashMap<Integer, FunctionHandler>(5000);
		fillFunctionHandlers();
	}

	abstract protected void fillFunctionHandlers();

	public void close() throws IOException {
		transport.close();
		transport = null;
	}

	public Long store(Object obj) {
		if (obj == null) {
			return new Long(-1);
		}
		Long id = idGenerator.getID(obj);
		Cell cell = cells.get(id);
		if (cell == null) {
			cell = new Cell(obj);
			cells.put(id, cell);
		}
		// else {
		// cell.incref();
		// }
		return id;
	}

	public Object load(Long id) {
		if (id < 0) {
			return null;
		}
		Cell cell = cells.get(id);
		return cell.obj;
	}

	protected void incref(Long id) {
		Cell cell = cells.get(id);
		if (cell != null) {
			cell.incref();
		}
	}

	protected void decref(Long id) {
		Cell cell = cells.get(id);
		if (cell != null) {
			if (cell.decref()) {
				cells.remove(id);
			}
		}
	}

	protected static String getExceptionTraceback(Exception exc) {
		StringWriter sw = new StringWriter(5000);
		PrintWriter pw = new PrintWriter(sw, true);
		exc.printStackTrace(pw);
		pw.flush();
		sw.flush();
		String[] lines = sw.toString().split("\r\n|\r|\n");
		StringWriter sw2 = new StringWriter(5000);
		// drop first line, it's the message, not traceback
		for (int i = 1; i < lines.length; i++) {
			sw2.write(lines[i]);
			sw2.write("\n");
		}
		return sw2.toString();
	}

	protected void sendProtocolException(ProtocolException exc) throws IOException {
		Builtin.Int8.pack(constants.REPLY_PROTOCOL_EXCEPTION, transport);
		Builtin.Str.pack(exc.toString(), transport);
	}

	protected void sendGenericException(GenericException exc)
			throws IOException {
		Builtin.Int8.pack(constants.REPLY_GENERIC_EXCEPTION, transport);
		Builtin.Str.pack(exc.message, transport);
		Builtin.Str.pack(exc.traceback, transport);
	}

	public void process() throws Exception {
		int seq = transport.beginRead();
		int cmdid = (Byte) (Builtin.Int8.unpack(transport));

		transport.beginWrite(seq);

		try {
			switch (cmdid) {
			case constants.CMD_INVOKE:
				processInvoke(seq);
				break;
			case constants.CMD_DECREF:
				processDecref(seq);
				break;
			case constants.CMD_INCREF:
				processIncref(seq);
				break;
			case constants.CMD_GETINFO:
				processGetInfo(seq);
				break;
			case constants.CMD_PING:
				processPing(seq);
				break;
			case constants.CMD_QUIT:
				processQuit(seq);
				break;
			default:
				throw new ProtocolException("unknown command code: " + cmdid);
			}
		} catch (ProtocolException exc) {
			transport.restartWrite();
			sendProtocolException(exc);
		} catch (GenericException exc) {
			transport.restartWrite();
			sendGenericException(exc);
		} catch (Exception ex) {
			transport.cancelWrite();
			throw ex;
		} finally {
			transport.endRead();
		}
		transport.endWrite();
	}

	protected void processDecref(Integer seq) throws IOException {
		Long id = (Long) (Builtin.Int64.unpack(transport));
		decref(id);
	}

	protected void processIncref(Integer seq) throws IOException {
		Long id = (Long) (Builtin.Int64.unpack(transport));
		incref(id);
	}

	protected void processQuit(Integer seq) throws IOException {
	}

	protected void processPing(Integer seq) throws IOException {
		String message = (String) (Builtin.Str.unpack(transport));
		Builtin.Int8.pack(constants.REPLY_SUCCESS, transport);
		Builtin.Str.pack(message, transport);
	}

	protected void processGetInfo(int seq) throws IOException {
		int code = (Integer) (Builtin.Int32.unpack(transport));
		HeteroMap map = new HeteroMap();

		switch (code) {
		case constants.INFO_SERVICE:
			processGetServiceInfo(map);
			break;
		case constants.INFO_FUNCTIONS:
			processGetFunctionsInfo(map);
			break;
		case constants.INFO_REFLECTION:
			processGetReflectionInfo(map);
			break;
		case constants.INFO_META:
			// fall-through
		default:
			processGetMetaInfo(map);
			break;
		}

		Builtin.Int8.pack(constants.REPLY_SUCCESS, transport);
		Builtin.heteroMapPacker.pack(map, transport);
	}

	protected abstract void processGetMetaInfo(HeteroMap map);
	protected abstract void processGetServiceInfo(HeteroMap map);
	protected abstract void processGetFunctionsInfo(HeteroMap map);
	protected abstract void processGetReflectionInfo(HeteroMap map);

	abstract protected void processInvoke(int seq) throws Exception;
}

