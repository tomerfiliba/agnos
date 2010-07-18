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
python srcgen.py
if [ ! $? -eq 0 ] ; then
	exit 1
fi
