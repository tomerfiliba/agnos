#!/bin/bash
python python.py
if [ $? -ne 0 ] ; then
	exit 1
fi
python java.py
if [ $? -ne 0 ] ; then
	exit 1
fi
python csharp.py
if [ $? -ne 0 ] ; then
	exit 1
fi
python cpp.py
if [ $? -ne 0 ] ; then
	exit 1
fi
python html.py
if [ $? -ne 0 ] ; then
	exit 1
fi
python pysrcgen.py
if [ $? -ne 0 ] ; then
	exit 1
fi
python restful.py
if [ $? -ne 0 ] ; then
    exit 1
fi
