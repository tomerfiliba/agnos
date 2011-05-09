#!/bin/bash

AGNOS_TOOLCHAIN_VERSION=`python -c "import agnos_compiler;print agnos_compiler.AGNOS_TOOLCHAIN_VERSION"`
cp compiler/src/agnos_compiler/version.py libagnos/python/src/agnos/version.py

if [ "$1" == "upload" ] ; then
	UPLOAD="yes"
else
	UPLOAD="no"
fi

if [ "$UPLOAD" == "yes" ]; then
	pushd tests
	./all.sh
	if [ $? -ne 0 ]; then
		echo "unit test failed"
		exit 1
	fi
	popd
fi

rm -rf release
mkdir release

###############################################################################
# compiler
###############################################################################

pushd compiler
rm -rf dist

python setup.py sdist --formats=gztar,zip
if [ $? -ne 0 ] ; then
    echo "buidling agnos_compiler failed gztar,zip"
    exit 1
fi

python setup.py bdist --formats=wininst --plat-name="win32"
if [ $? -ne 0 ] ; then
    echo "buidling agnos_compiler failed wininst"
    exit 1
fi

rm -rf build
popd
mkdir release/agnos_compiler
cp compiler/dist/* release/agnos_compiler
rm -rf compiler/dist

###############################################################################
# python
###############################################################################

pushd libagnos/python
rm -rf dist

python setup.py sdist --formats=gztar,zip
if [ $? -ne 0 ] ; then
    echo "buidling libagnos-python failed gztar,zip"
    exit 1
fi

python setup.py bdist --formats=wininst --plat-name="win32"
if [ $? -ne 0 ] ; then
    echo "buidling libagnos-python failed wininst"
    exit 1
fi

rm -rf build
cd dist
popd

mkdir -p release/libagnos/python
cp libagnos/python/dist/* release/libagnos/python
rm -rf libagnos/python/dist &> /dev/null

###############################################################################
# java
###############################################################################
mkdir -p release/agnos-java/src
mkdir -p release/libagnos/java

cp -R libagnos/java/src/ release/agnos-java/
cp libagnos/java/SConstruct release/agnos-java/
pushd release
tar -czf libagnos-$AGNOS_TOOLCHAIN_VERSION-java-src.tar.gz agnos-java
zip -r libagnos-$AGNOS_TOOLCHAIN_VERSION-java-src.zip agnos-java

pushd agnos-java
scons
mv doc agnos-java
zip -r libagnos-$AGNOS_TOOLCHAIN_VERSION-java-doc.zip agnos-java
popd

mv libagnos-*.* libagnos/java
mv agnos-java/libagnos-*.* libagnos/java
mv agnos-java/agnos.jar libagnos/java/agnos.jar
rm -rf agnos-java
popd


###############################################################################
# C#
###############################################################################
mkdir -p release/agnos-csharp/src/Properties
mkdir -p release/libagnos/csharp

cp libagnos/csharp/src/*.cs release/agnos-csharp/src/
cp libagnos/csharp/src/Properties/*.cs release/agnos-csharp/src/Properties/
cp libagnos/csharp/src/*.csproj release/agnos-csharp/src/
cp libagnos/csharp/src/*.sln release/agnos-csharp/src/

pushd release
tar -czf libagnos-$AGNOS_TOOLCHAIN_VERSION-csharp-src.tar.gz agnos-csharp
zip -r libagnos-$AGNOS_TOOLCHAIN_VERSION-csharp-src.zip agnos-csharp
mv libagnos-*.* libagnos/csharp/

pushd agnos-csharp/src
xbuild Agnos.sln # /p:DocumentationFile=agnos-doc.xml
popd
mv agnos-csharp/src/bin/*/Agnos.dll libagnos/csharp/
rm -rf agnos-csharp
popd


###############################################################################
# C++
###############################################################################
mkdir -p release/agnos-cpp/src
mkdir -p release/libagnos/cpp

cp libagnos/cpp/*.sln release/agnos-cpp/
cp libagnos/cpp/*.vcxproj release/agnos-cpp/
cp libagnos/cpp/SConstruct release/agnos-cpp/
cp libagnos/cpp/src/*.cpp release/agnos-cpp/src/
cp libagnos/cpp/src/*.hpp release/agnos-cpp/src/

pushd release
tar -czf libagnos-$AGNOS_TOOLCHAIN_VERSION-cpp-src.tar.gz agnos-cpp
zip -r libagnos-$AGNOS_TOOLCHAIN_VERSION-cpp-src.zip agnos-cpp
mv libagnos-*.* libagnos/cpp/

if [ "$UPLOAD" == "yes" ]; then
	pushd agnos-cpp
	scons

	if [ $? -ne 0 ]; then
	   echo "c++ scons failed"
	   exit 1
	fi

	popd
fi

rm -rf agnos-cpp
popd


###############################################################################
# upload
###############################################################################

echo "=========================================================================="
echo "uploading to sourceforge. ENTER to continue, CTRL+C to skip"
read

rsync -rv release/ gangesmaster,agnos@frs.sourceforge.net:/home/frs/project/a/ag/agnos/$AGNOS_TOOLCHAIN_VERSION/


