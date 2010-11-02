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

import java.util.*;


public abstract class RefList implements List
{
	/*protected final Long objref;
	protected final ClientUtils utils;
	protected final Packers.AbstractPacker packer;
	
	protected RefList(ClientUtils utils, Long objref, Packers.AbstractPacker packer) {
		this.utils = utils;
		this.objref = objref;
		this.packer = packer;
	}
	public void add(int index, Object element) {
		int seq = utils.getSeq();
		utils.transport.beginWrite(seq);
		Packers.Int8.pack(CMD_INVOKE, utils.transport);
		Packers.Int32.pack(funcid, utils.transport);
		replies.put(seq, new ReplySlot(packer));
	}
	public void add(Object element) {
		
	}*/
}

