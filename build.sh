#!/bin/bash

AGNOS_TOOLCHAIN_VERSION=`python -c "import agnos_compiler;print agnos_compiler.AGNOS_TOOLCHAIN_VERSION"`

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
rm setup.py &> /dev/null
sed -e "s/__AGNOS_TOOLCHAIN_VERSION__/$AGNOS_TOOLCHAIN_VERSION/" _setup.py > setup.py
python setup.py sdist --formats=gztar,zip

if [ $? -ne 0 ] ; then
    echo "buidling agnos_compiler failed gztar,zip"
    exit 1
fi

python2.6 setup.py bdist --formats=egg,wininst --plat-name="win32"
if [ $? -ne 0 ] ; then
    echo "buidling agnos_compiler failed egg-2.6,wininst"
    exit 1
fi

python2.7 setup.py bdist --formats=egg
if [ $? -ne 0 ] ; then
    echo "buidling agnos_compiler failed egg-2.7"
    exit 1
fi

#python3.0 setup.py bdist --formats=egg
#if [ $? -ne 0 ] ; then
#    echo "buidling agnos_compiler failed egg-3.0"
#    exit 1
#fi

#python3.1 setup.py bdist --formats=egg
#if [ $? -ne 0 ] ; then
#    echo "buidling agnos_compiler failed egg-3.1"
#    exit 1
#fi

rm setup.py &> /dev/null

rm -rf build
rm -rf src/*.egg-info
popd
mkdir release/agnos_compiler
cp compiler/dist/* release/agnos_compiler
rm -rf compiler/dist

###############################################################################
# python
###############################################################################

pushd libagnos/python
rm -rf dist
rm setup.py &> /dev/null
sed -e "s/__AGNOS_TOOLCHAIN_VERSION__/$AGNOS_TOOLCHAIN_VERSION/" _setup.py > setup.py

python setup.py sdist --formats=gztar,zip

if [ $? -ne 0 ] ; then
    echo "buidling libagnos-python failed gztar,zip"
    exit 1
fi

python2.6 setup.py bdist --formats=egg,wininst --plat-name="win32"
if [ $? -ne 0 ] ; then
    echo "buidling libagnos-python failed egg-2.6,wininst"
    exit 1
fi

python2.7 setup.py bdist --formats=egg
if [ $? -ne 0 ] ; then
    echo "buidling libagnos-python failed egg-2.7"
    exit 1
fi

#python3.0 setup.py bdist --formats=egg
#if [ $? -ne 0 ] ; then
#    echo "buidling libagnos-python failed egg-3.0"
#    exit 1
#fi

#python3.1 setup.py bdist --formats=egg
#if [ $? -ne 0 ] ; then
#    echo "buidling libagnos-python failed egg-3.1"
#    exit 1
#fi

rm setup.py &> /dev/null
rm -rf build
rm -rf *.egg-info
rm -rf src/*.egg-info
cd dist
# rename 's/(.+)-[^-]+\.([twz].*)/lib$1-$AGNOS_TOOLCHAIN_VERSION-python.$2/' *
# rename 's/(.+)-[^-]+\-py(.+)\.egg/lib$1-$AGNOS_TOOLCHAIN_VERSION-python-$2.egg/' *.egg
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

if [ "$UPLOAD" != "yes" ]; then
	exit
fi

echo "=========================================================================="
echo "uploading to sourceforge. ENTER to continue, CTRL+C to skip"
read

rsync -v release/ gangesmaster,agnos@frs.sourceforge.net:/home/frs/project/a/ag/agnos/$AGNOS_TOOLCHAIN_VERSION/



