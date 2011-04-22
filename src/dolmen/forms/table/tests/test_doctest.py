# -*- coding: utf-8 -*-

import unittest
import doctest


def test_suite():
    optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    globs = {}

    suite = unittest.TestSuite()
    for filename in ['forms.txt',]:
        test = doctest.DocFileSuite(
            filename, optionflags=optionflags, globs=globs)
        suite.addTest(test)

    return suite
