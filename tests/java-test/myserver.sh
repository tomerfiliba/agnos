#!/bin/sh
exec java -cp /home/tomer/workspace/agnos_toolchain/libagnos/java/agnos.jar:bindings/FeatureTest.jar:test.jar myserver "$@"
