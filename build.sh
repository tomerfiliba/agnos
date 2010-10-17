#!/bin/bash

AGNOS_TOOLCHAIN_VERSION=`python -c "import agnos_compiler;print agnos_compiler.AGNOS_TOOLCHAIN_VERSION"`

rm -rf release
mkdir release

###############################################################################
# compiler
###############################################################################

pushd agnos_compiler
rm -rf dist
rm setup.py
sed -e "s/__AGNOS_TOOLCHAIN_VERSION__/$AGNOS_TOOLCHAIN_VERSION/" _setup.py > setup.py
python setup.py sdist --formats=gztar,zip
python setup.py bdist --formats=egg,wininst --plat-name="win32"
rm setup.py
rm -rf build
rm -rf *.egg-info
popd
cp agnos_compiler/dist/* release
rm -rf agnos_compiler/dist

###############################################################################
# python
###############################################################################

pushd libagnos/python
rm -rf dist
rm setup.py
sed -e "s/__AGNOS_TOOLCHAIN_VERSION__/$AGNOS_TOOLCHAIN_VERSION/" _setup.py > setup.py
python setup.py sdist --formats=gztar,zip
python setup.py bdist --formats=egg,wininst --plat-name="win32"
rm setup.py
rm -rf build
rm -rf *.egg-info
cd dist
#rename 's/(.+)-[^-]+\.([twz].*)/lib$1-python.$2/' *
#rename 's/(.+)-[^-]+\-py(.+)\.egg/lib$1-python-$2.egg/' *.egg
popd
mkdir release/python
cp libagnos/python/dist/* release/python
rm -rf libagnos/python/dist


###############################################################################
# java
###############################################################################
mkdir -p release/agnos-java/src
mkdir release/java

cp libagnos/java/src/*.java release/agnos-java/src/
cp libagnos/java/SConstruct release/agnos-java/
pushd release
tar -czf libagnos-java.tar.gz agnos-java
zip -r libagnos-java.zip agnos-java
pushd agnos-java
scons
popd
mv libagnos-java.* java
mv agnos-java/agnos.jar java/agnos.jar
rm -rf agnos-java
popd


###############################################################################
# C#
###############################################################################
mkdir -p release/agnos-csharp/src
mkdir    release/agnos-csharp/src/Properties
mkdir release/csharp

cp libagnos/csharp/src/*.cs release/agnos-csharp/src/
cp libagnos/csharp/src/Properties/*.cs release/agnos-csharp/src/Properties/
cp libagnos/csharp/src/*.csproj release/agnos-csharp/src/
cp libagnos/csharp/src/*.sln release/agnos-csharp/src/

pushd release
tar -czf libagnos-csharp.tar.gz agnos-csharp 
zip -r libagnos-csharp.zip agnos-csharp
mv libagnos-csharp.* csharp

pushd agnos-csharp/src
xbuild Agnos.sln
popd
mv agnos-csharp/src/bin/*/Agnos.dll csharp
rm -rf agnos-csharp
popd


###############################################################################
# C++
###############################################################################
mkdir -p release/agnos-cpp/src
mkdir release/cpp

cp libagnos/cpp/*.sln release/agnos-cpp/
cp libagnos/cpp/*.vcxproj release/agnos-cpp/
cp libagnos/cpp/SConstruct release/agnos-cpp/
cp libagnos/cpp/src/*.cpp release/agnos-cpp/src/
cp libagnos/cpp/src/*.hpp release/agnos-cpp/src/

pushd release
tar -czf libagnos-cpp.tar.gz agnos-cpp 
zip -r libagnos-cpp.zip agnos-cpp
mv libagnos-cpp.* cpp
pushd agnos-cpp
scons
popd
rm -rf agnos-cpp
popd

###############################################################################
# wrap it up
###############################################################################
pushd release

mkdir agnos-toolchain-win32
mkdir agnos-toolchain-win32/cpp
mkdir agnos-toolchain-win32/csharp
mkdir agnos-toolchain-win32/java
mkdir agnos-toolchain-win32/python

cp *.zip *.exe *.egg agnos-toolchain-win32
cp cpp/*.zip agnos-toolchain-win32/cpp
cp csharp/*.zip csharp/*.dll agnos-toolchain-win32/csharp
cp java/*.zip java/*.jar agnos-toolchain-win32/java
cp python/*.zip python/*.exe python/*.egg agnos-toolchain-win32/python

zip -r agnos-toolchain-win32.zip agnos-toolchain-win32
rm -rf agnos-toolchain-win32

mkdir agnos-toolchain-posix
mkdir agnos-toolchain-posix/cpp
mkdir agnos-toolchain-posix/csharp
mkdir agnos-toolchain-posix/java
mkdir agnos-toolchain-posix/python

cp *.tar.gz *.egg agnos-toolchain-posix
cp cpp/*.tar.gz agnos-toolchain-posix/cpp
cp csharp/*.tar.gz csharp/*.dll agnos-toolchain-posix/csharp
cp java/*.tar.gz java/*.jar agnos-toolchain-posix/java
cp python/*.tar.gz python/*.egg agnos-toolchain-posix/python

tar -czf agnos-toolchain-posix.tar.gz agnos-toolchain-posix
rm -rf agnos-toolchain-posix

rm agnos_compiler*
rm -rf cpp
rm -rf csharp
rm -rf java
rm -rf python

popd




