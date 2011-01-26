// ////////////////////////////////////////////////////////////////////////////
// Part of the Agnos RPC Framework
// http://agnos.sourceforge.net
//
// Copyright 2011, International Business Machines Corp.
// Author: Tomer Filiba (tomerf@il.ibm.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// ////////////////////////////////////////////////////////////////////////////

package agnos.transports;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Arrays;


/**
 * Process-backed transport. This class spawns the server as a child process
 * and connects to it over a socket. Theoretically it would be better to
 * rely on pipes or unix-domain sockets, but it's not practical or feasible on
 * all platforms and languages -- and besides, localhost sockets are highly
 * optimized on both Linux and Windows, and it shouldn't impose any overheads.
 * 
 * @author Tomer Filiba
 * 
 */
public class ProcTransport extends WrappedTransport
{
	public Process proc;

	/**
	 * Constructs a ProcTransport instance from a running server process an
	 * open transport (that's connected to that process). You should use one
	 * of the connect() factory methods instead of using this constructor
	 * directly.
	 * 
	 * @param proc
	 *            The running process instance
	 * @param transport
	 *            The open transport instance (assumed to be connected to that
	 *            process)
	 */
	public ProcTransport(Process proc, ITransport transport)
	{
		super(transport);
		this.proc = proc;
	}

	/**
	 * Spawns a process (given as a filename) with the default command-line
	 * arguments ("-m lib"), and connects to it.
	 * 
	 * @param filename
	 *            The file name of the exectuable (e.g., "c:\\foo\\bar.exe")
	 * 
	 * @return The ProcTransport instance
	 */
	public static ProcTransport connect(String filename) throws Exception
	{
		return connect(filename, "-m", "lib");
	}

	/**
	 * Spawns a process (given as a filename) with the the given command-line
	 * arguments, and connects to it.
	 * 
	 * @param filename
	 *            The file name of the exectuable (e.g., "c:\\foo\\bar.exe")
	 * 
	 * @param args
	 *            The command-line arguments (given as varargs)
	 * 
	 * @return The ProcTransport instance
	 */
	public static ProcTransport connect(String filename, String... args)
			throws Exception
	{
		ArrayList<String> cmdline = new ArrayList<String>();
		cmdline.add(filename);
		cmdline.addAll(Arrays.asList(args));
		ProcessBuilder pb = new ProcessBuilder(cmdline);
		pb.redirectErrorStream(true);
		return connect(pb);
	}

	/**
	 * Spawns a process (given as a ProcessBuilder) and connects to it.
	 * 
	 * @param procbuilder
	 *            The ProcessBuilder instance
	 * 
	 * @return The ProcTransport instance
	 */	public static ProcTransport connect(ProcessBuilder procbuilder)
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

			sb.append("Process " + proc
					+ " either failed to start or is not an Agnos server");
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

		return new ProcTransport(proc, new SocketTransport(hostname, port,
				SocketTransport.DEFAULT_BUFFER_SIZE));
	}
}
