#!/bin/bash
python python.py
if [ ! $? -eq 0 ] ; then
	exit 1
fi
python java.py
if [ ! $? -eq 0 ] ; then
	exit 1
fi
python csharp.py
if [ ! $? -eq 0 ] ; then
	exit 1
fi
python pysrcgen.py
if [ ! $? -eq 0 ] ; then
	exit 1
fi
python html.py
if [ ! $? -eq 0 ] ; then
	exit 1
fi
