using System;
using System.Threading;

namespace Agnos.Utils
{
    public class ReentrantLock
    {
        protected volatile Thread owner;

        public ReentrantLock()
        {
            owner = null;
        }

        public void Acquire()
        {
            Monitor.Enter(this);
            owner = Thread.CurrentThread;
        }

        public void Release()
        {
            owner = null;
            Monitor.Exit(this);
        }

        public bool IsHeldByCurrentThread()
        {
            return owner == Thread.CurrentThread;
        }
    }


}
