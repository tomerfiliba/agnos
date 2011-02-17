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

using System;
using System.IO;
using System.Threading;

namespace Agnos.Utils
{
    public sealed class ReentrantLock
    {
        private volatile Thread owner;
        private int count;

        public ReentrantLock()
        {
            owner = null;
            count = 0;
        }
        
        public void Acquire()
        {
            Monitor.Enter(this);
            owner = Thread.CurrentThread;
            count += 1;
        }

        public void Release()
        {
    		count -= 1;
    		if (count == 0) {
        		owner = null;
        	}
        	if (count < 0) {
				count = 0;
        		throw new InvalidOperationException("released too many times!");
        	}
            Monitor.Exit(this);
        }

        public bool IsHeldByCurrentThread()
        {
            return owner == Thread.CurrentThread;
        }
    }
    
    public sealed class BoundInputStream : Stream
    {
    
    	private int remaining_length;
    	private Stream stream;
    	private bool skip_underlying;
    	private bool close_underlying;
    	
    	public BoundInputStream(Stream stream, int length, bool skip_underlying, bool close_underlying)
    	{
    		this.stream = stream;
    		this.remaining_length = length;
    		this.skip_underlying = skip_underlying;
    		this.close_underlying = close_underlying;
    	}

    	public override void Close() 
    	{
    		if (stream == null) {
    			return;
    		}
    		if (skip_underlying) {
    			Skip(-1);
    		}
    		if (close_underlying) {
    			stream.Close();
    		}
    		stream = null;
    	}
    	
    	public int Available
    	{
    		get {
    			return remaining_length;
    		}
    	}
    	
    	public override int Read(byte[] data, int offset, int count)
    	{
    		if (count < 0) {
    			throw new ArgumentOutOfRangeException("count must be >= 0");
    		}
    		if (count > remaining_length) {
    			count = remaining_length;
    		}
    		if (count <= 0) {
    			return 0;
    		}
    		int actual = stream.Read(data, offset, count);
    		remaining_length -= actual;
    		return actual;
    	}
    	
    	public int Skip(int count)
    	{
    		byte[] tmp = new byte[16 * 1024];
    		if (count < 0) {
    			count = remaining_length;
    		}
    		int total_skipped = 0;
    		while (count > 0) {
    			int len = stream.Read(tmp, 0, (count > tmp.Length) ? tmp.Length : count);
    			if (len <= 0) {
    				remaining_length = 0;
    				break;
    			}
    			total_skipped += len;
    			count -= len;
    			remaining_length -= len;
    		}
    		return total_skipped;
    	}

		//
    	// Stream interface
    	//
		public override void Write (byte[] buffer, int offset, int count)
		{
			throw new IOException ("not implemented");
		}
		public override bool CanRead {
			get { return true; }
		}
		public override bool CanSeek {
			get { return false; }
		}
		public override bool CanWrite {
			get { return false; }
		}
		public override long Length {
			get {
				throw new IOException ("not implemented");
			}
		}
		public override long Position {
			get {
				throw new IOException ("not implemented");
			}
			set {
				throw new IOException ("not implemented");
			}
		}
		public override void SetLength (long value)
		{
			throw new IOException ("not implemented");
		}
		public override long Seek (long offset, SeekOrigin origin)
		{
			throw new IOException ("not implemented");
		}
		public override void Flush ()
		{
			throw new IOException ("not implemented");
		}

    }


}


