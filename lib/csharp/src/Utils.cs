using System;
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


}


