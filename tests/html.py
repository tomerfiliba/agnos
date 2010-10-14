import os
import sys
import signal
import unittest
import time
from base import TargetTest


class TestCSharp(TargetTest):
    def runTest(self):
        self.run_agnosc("doc", "ut/features.xml", "ut/gen-html")



if __name__ == '__main__':
    unittest.main()
