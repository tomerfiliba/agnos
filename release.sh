#!/bin/bash

rm -rf release

###############################################################################
# compiler
###############################################################################

rm -rf dist
python setup.py bdist --formats=gztar,zip,egg,wininst
cp dist/* release/
rm -rf dist

###############################################################################
# java
###############################################################################
mkdir -p release/tmp/src

cp lib/java/src/*.java release/tmp/src/
cp lib/java/src/SConstruct release/tmp/
tar -czf release/libagnos-java.tar.gz release/tmp 
zip -r release/libagnos-java.zip release/tmp
rm -rf release/tmp

pushd lib/java
scons -c
scons
popd
cp lib/java/agnos.jar release/libagnos.jar

exit

###############################################################################
# C#
###############################################################################
mkdir -p release/tmp/src
mkdir release/tmp/src/Properties

cp lib/csharp/src/*.cs release/tmp/src/
cp lib/csharp/src/Properties/*.cs release/tmp/src/Properties/
cp lib/csharp/src/*.csproj release/tmp/src/
cp lib/csharp/src/*.sln release/tmp/src/

tar -czf release/libagnos-csharp.tar.gz release/tmp 
zip -r release/libagnos-csharp.zip release/tmp
rm -rf release/tmp

pushd lib/csharp/src
xbuild Agnos.sln
popd
cp lib/csharp/src/bin/Release/Agnos.dll release/libagnos-mono.dll

###############################################################################
# C++
###############################################################################
mkdir -p release/tmp/src

cp lib/cpp/*.sln release/tmp/
cp lib/cpp/*.vcxpro release/tmp/
cp lib/cpp/SConstruct release/tmp/
cp lib/cpp/src/*.cpp release/tmp/src/
cp lib/cpp/src/*.hpp release/tmp/src/

tar -czf release/libagnos-cpp.tar.gz release/tmp 
zip -r release/libagnos-cpp.zip release/tmp
rm -rf release/tmp

###############################################################################
# python
###############################################################################
mkdir -p release/tmp/src

pushd lib/python
rm -rf dist
python setup.py bdist --formats=gztar,zip,egg,wininst
popd
cp lib/python/dist/* release/


###############################################################################
# wrap it up
###############################################################################
pushd release
mkdir agnos-toolchain
cp *.zip *.exe *.dll *.jar agnos-toolchain
zip -r agnos-toolchain.zip agnos-toolchain
rm -rf tmp
mkdir agnos-toolchain
cp *.tar.gz *.exe *.dll *.jar agnos-toolchain
tar -czf agnos-toolchain.tar.gz agnos-toolchain











