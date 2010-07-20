#!/bin/bash
ROOT=`pwd`/..
export PATH=$PATH:$ROOT/bin

echo "generating IDL"
agnos-srcgen.py mextra -o autogen

echo "generating java bindings"
agnosc.py autogen/Mextra_autogen.xml -t java -o javaclient

echo "building agnos.jar"
pushd $ROOT/lib/java &> /dev/null
ant jar
popd &> /dev/null

echo "building MextraBindings.jar"
cd javaclient
rm -rf build &> /dev/null
mkdir build
javac -g -cp $ROOT/lib/java/build/jars/agnos.jar -d build Mextra/*/*.java
cd build
jar cf MextraBindings.jar .
cd ..
mv build/MextraBindings.jar .
cd ..

echo "building Demo.jar"
cd javaclient
rm -rf build &> /dev/null
mkdir build
javac -g -cp $ROOT/lib/java/build/jars/agnos.jar:MextraBindings.jar -d build Demo.java
cd build
jar cf Demo.jar .
cd ..
mv build/Demo.jar .
cd ..

echo "running server"
PYTHONPATH=$PYTHONPATH:`pwd` python autogen/Mextra_autogen_server.py -h localhost -p 17788 &
SERVERPID=$!
sleep 1

echo "running demo"
echo "------------------------------------------------------------------------"
java -cp $ROOT/lib/java/build/jars/agnos.jar:javaclient/MextraBindings.jar:javaclient/Demo.jar Demo localhost 17788
echo "------------------------------------------------------------------------"

echo "killing the server"
pkill -P $SERVERPID


