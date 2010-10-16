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

