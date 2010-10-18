#!/bin/bash
ROOT=`pwd`/..
export PATH=$PATH:$ROOT/bin

echo "generating IDL"
agnosrc-py mextra -o autogen

echo "generating C# bindings"
agnosc.py autogen/Mextra_autogen.xml -t cs -o csclient/Mextra

echo "building project"
xbuild /verbosity:quiet csclient/csclient.sln 

echo "running server"
PYTHONPATH=$PYTHONPATH:`pwd` python autogen/Mextra_autogen_server.py -h localhost -p 17789 &
SERVERPID=$!
sleep 1

echo "running demo"
echo "------------------------------------------------------------------------"
csclient/bin/Debug/csclient.exe localhost 17789
echo "------------------------------------------------------------------------"

echo "killing the server"
pkill -P $SERVERPID


