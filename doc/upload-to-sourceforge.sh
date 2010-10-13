#!/bin/sh

make html
if [ $? -ne 0 ]; then
    echo "--make html failed--"
    exit 1
fi

rsync -r -v _build/html/ gangesmaster,agnos@shell.sourceforge.net:/home/groups/a/ag/agnos/htdocs

if [ $? -ne 0 ]; then
    echo "--rsync failed--"
    exit 1
fi
