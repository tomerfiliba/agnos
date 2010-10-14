#!/bin/sh
exec java -cp /home/tomer/workspace/agnos_compiler/lib/java/agnos.jar:bindings/FeatureTest.jar:test.jar myclient "$@"
