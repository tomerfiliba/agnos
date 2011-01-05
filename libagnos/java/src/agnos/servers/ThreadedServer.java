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

package agnos.servers;

import agnos.protocol.BaseProcessor;
import agnos.protocol.IProcessorFactory;
import agnos.transportFactories.ITransportFactory;


public class ThreadedServer extends BaseServer
{
	public ThreadedServer(IProcessorFactory processorFactory,
			ITransportFactory transportFactory)
	{
		super(processorFactory, transportFactory);
	}

	@Override
	protected void serveClient(final BaseProcessor processor) throws Exception
	{
		Thread t = new Thread() {
			public void run()
			{
				try {
					BaseServer._serveClient(processor);
				} catch (Exception ex) {
					// should log this somehow
				}
			}
		};
		t.start();
	}
}

