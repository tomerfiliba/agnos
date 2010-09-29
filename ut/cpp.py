import os
import sys
import signal
import unittest
import time
from base import TargetTest


class TestCSharp(TargetTest):
    def runTest(self):
        self.run_agnosc("c++", "ut/simple.xml", "ut/cpp-test/bindings")



if __name__ == '__main__':
    unittest.main()
