##############################################################################
#
# Copyright (c) 2004-2008 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test harness for the test runner itself.
"""
from __future__ import print_function

import re
import gc
import os
import sys
import unittest

import doctest
from zope.testing import renormalizing


#separated checkers for the different platform,
#because it s...s to maintain just one
if sys.platform == 'win32':
    checker = renormalizing.RENormalizing([
        # 2.5 changed the way pdb reports exceptions
        (re.compile(r"<class 'exceptions.(\w+)Error'>:"),
                    r'exceptions.\1Error:'),

        #rewrite pdb prompt to ... the current location
        #windows, py2.4 pdb seems not to put the '>' on doctest locations
        #therefore we cut it here
        (re.compile('^> doctest[^\n]+->None$', re.M), '...->None'),

        #rewrite pdb prompt to ... the current location
        (re.compile('^> [^\n]+->None$', re.M), '> ...->None'),

        (re.compile(r"<module>"),(r'?')),
        (re.compile(r"<type 'exceptions.(\w+)Error'>:"),
                    r'exceptions.\1Error:'),

        # testtools content formatter is used to mime-encode
        # tracebacks when the SubunitOutputFormatter is used, and the
        # resulting text includes a size which can vary depending on
        # the path included in the traceback.
        (re.compile(r'traceback\n[A-F\d]+', re.MULTILINE),
         r'traceback\nNNN'),

        (re.compile("'[A-Za-z]:\\\\"), "'"), # hopefully, we'll make Windows happy
                                             # replaces drives with nothing

        (re.compile(r'\\\\'), '/'), # more Windows happiness
                                    # double backslashes in coverage???

        (re.compile(r'\\'), '/'), # even more Windows happiness
                                  # replaces backslashes in paths

        (re.compile(r'/r$', re.MULTILINE), '\\r'), # undo some of that

        #this is a magic to put linefeeds into the doctest
        (re.compile('##r##\n'), '\r'),

        (re.compile(r'\d+[.]\d\d\d seconds'), 'N.NNN seconds'),
        (re.compile(r'\d+[.]\d\d\d s'), 'N.NNN s'),
        (re.compile(r'\d+[.]\d\d\d{'), 'N.NNN{'),
        (re.compile(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+'),
         'YYYY-MM-DD HH:MM:SS.mmmmmm'),
        (re.compile('( |")[^\n]+testrunner-ex'), r'\1testrunner-ex'),
        (re.compile('( |")[^\n]+testrunner.py'), r'\1testrunner.py'),
        (re.compile(r'> [^\n]*(doc|unit)test[.]py\(\d+\)'),
                    r'\1test.py(NNN)'),
        (re.compile(r'[.]py\(\d+\)'), r'.py(NNN)'),
        (re.compile(r'[.]py:\d+'), r'.py:NNN'),
        (re.compile(r' line \d+,', re.IGNORECASE), r' Line NNN,'),
        (re.compile(r' line {([a-z]+)}\d+{', re.IGNORECASE), r' Line {\1}NNN{'),

        # omit traceback entries for unittest.py or doctest.py (and
        # their package variants) from output:
        (re.compile(r'^ +File "[^\n]*(doctest|unittest|case)(/__init__)?.py", [^\n]+\n[^\n]+\n',
                    re.MULTILINE),
         r''),
        (re.compile(r'^{\w+} +File "{\w+}[^\n]*(doctest|unittest|case)(/__init__)?.py{\w+}", [^\n]+\n[^\n]+\n',
                    re.MULTILINE),
         r''),
        #(re.compile('^> [^\n]+->None$', re.M), '> ...->None'),
        (re.compile('import pdb; pdb'), 'Pdb()'), # Py 2.3

        # Python 3 exceptions are from the builtins module
        (re.compile(r'builtins\.(SyntaxError|TypeError)'),
         r'exceptions.\1'),

        # Python 3.3 has better exception messages
        (re.compile("ImportError: No module named '(?:[^']*[.])?([^'.]*)'"),
         r'ImportError: No module named \1'),

        # PyPy has different exception messages too
        (re.compile("ImportError: No module named (?:[a-zA-Z_0-9.]*[.])?([a-zA-Z_0-9]*)"),
         r'ImportError: No module named \1'),
        (re.compile("NameError: global name '([^']*)' is not defined"),
         r"NameError: name '\1' is not defined"),

        ])
else:
    #*nix
    checker = renormalizing.RENormalizing([
        # 2.5 changed the way pdb reports exceptions
        (re.compile(r"<class 'exceptions.(\w+)Error'>:"),
                    r'exceptions.\1Error:'),

        #rewrite pdb prompt to ... the current location
        (re.compile('^> [^\n]+->None$', re.M), '> ...->None'),

        (re.compile(r"<module>"),(r'?')),
        (re.compile(r"<type 'exceptions.(\w+)Error'>:"),
                    r'exceptions.\1Error:'),

        #this is a magic to put linefeeds into the doctest
        #on win it takes one step, linux is crazy about the same...
        (re.compile('##r##'), r'\r'),
        (re.compile(r'\r'), '\\\\r\n'),

        (re.compile(r'\d+[.]\d\d\d seconds'), 'N.NNN seconds'),
        (re.compile(r'\d+[.]\d\d\d s'), 'N.NNN s'),
        (re.compile(r'\d+[.]\d\d\d{'), 'N.NNN{'),
        (re.compile(r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+'),
         'YYYY-MM-DD HH:MM:SS.mmmmmm'),
        (re.compile('( |")[^\n]+testrunner-ex'), r'\1testrunner-ex'),
        (re.compile('( |")[^\n]+testrunner.py'), r'\1testrunner.py'),
        (re.compile(r'> [^\n]*(doc|unit)test[.]py\(\d+\)'),
                    r'\1test.py(NNN)'),
        (re.compile(r'[.]py\(\d+\)'), r'.py(NNN)'),
        (re.compile(r'[.]py:\d+'), r'.py:NNN'),
        (re.compile(r' line \d+,', re.IGNORECASE), r' Line NNN,'),
        (re.compile(r' line {([a-z]+)}\d+{', re.IGNORECASE), r' Line {\1}NNN{'),

        # testtools content formatter is used to mime-encode
        # tracebacks when the SubunitOutputFormatter is used, and the
        # resulting text includes a size which can vary depending on
        # the path included in the traceback.
        (re.compile(r'traceback\n[A-F\d]+', re.MULTILINE),
         r'traceback\nNNN'),

        # omit traceback entries for unittest.py or doctest.py (and
        # their package variants) from output:
        (re.compile(r'^ +File "[^\n]*(doctest|unittest|case)(/__init__)?.py", [^\n]+\n[^\n]+\n',
                    re.MULTILINE),
         r''),
        (re.compile(r'^{\w+} +File "{\w+}[^\n]*(doctest|unittest|case)(/__init__)?.py{\w+}", [^\n]+\n[^\n]+\n',
                    re.MULTILINE),
         r''),
        (re.compile('import pdb; pdb'), 'Pdb()'), # Py 2.3

        # Python 3 exceptions are from the builtins module
        (re.compile(r'builtins\.(SyntaxError|TypeError)'),
         r'exceptions.\1'),

        # Python 3.3 has better exception messages
        (re.compile("ImportError: No module named '(?:[^']*[.])?([^'.]*)'"),
         r'ImportError: No module named \1'),

        # PyPy has different exception messages too
        (re.compile("ImportError: No module named (?:[a-zA-Z_0-9.]*[.])?([a-zA-Z_0-9]*)"),
         r'ImportError: No module named \1'),
        (re.compile("NameError: global name '([^']*)' is not defined"),
         r"NameError: name '\1' is not defined"),

        ])

def setUp(test):
    test.globs['print_function'] = print_function
    test.globs['saved-sys-info'] = (
        sys.path[:],
        sys.argv[:],
        sys.modules.copy(),
    )
    if hasattr(gc, 'get_threshold'):
        test.globs['saved-gc-threshold'] = gc.get_threshold()
    test.globs['this_directory'] = os.path.split(__file__)[0]
    test.globs['testrunner_script'] = sys.argv[0]


def tearDown(test):
    sys.path[:], sys.argv[:] = test.globs['saved-sys-info'][:2]
    if hasattr(gc, 'get_threshold'):
        gc.set_threshold(*test.globs['saved-gc-threshold'])
    sys.modules.clear()
    sys.modules.update(test.globs['saved-sys-info'][2])


def test_suite():
    suites = [
        doctest.DocFileSuite(
        'testrunner-arguments.txt',
        'testrunner-coverage.txt',
        'testrunner-debugging-layer-setup.test',
        'testrunner-debugging-import-failure.test',
        'testrunner-debugging.txt',
        'testrunner-edge-cases.txt',
        'testrunner-errors.txt',
        'testrunner-layers-buff.txt',
        'testrunner-layers-ntd.txt',
        'testrunner-layers.txt',
        'testrunner-layers-api.txt',
        'testrunner-progress.txt',
        'testrunner-colors.txt',
        'testrunner-simple.txt',
        'testrunner-test-selection.txt',
        'testrunner-verbose.txt',
        'testrunner-repeat.txt',
        'testrunner-knit.txt',
        'testrunner-shuffle.txt',
        'testrunner-eggsupport.txt',
        setUp=setUp, tearDown=tearDown,
        optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
        checker=checker),
        doctest.DocTestSuite('zope.testrunner'),
        doctest.DocTestSuite('zope.testrunner.coverage',
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE),
        doctest.DocTestSuite('zope.testrunner.options'),
        doctest.DocTestSuite('zope.testrunner.find'),
        ]

    # PyPy uses a different garbage collector
    if hasattr(gc, 'get_threshold'):
        suites.append(
            doctest.DocFileSuite(
            'testrunner-gc.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
            checker=checker))

    # PyPy does not support sourceless imports, apparently (tried version 1.9)
    if 'PyPy' not in sys.version:
        suites.append(
            doctest.DocFileSuite(
            'testrunner-wo-source.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
            checker=checker))

    if sys.platform == 'win32':
        suites.append(
            doctest.DocFileSuite(
            'testrunner-coverage-win32.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
            checker=checker))

    # Python <= 2.4.1 had a bug that prevented hotshot from running in
    # non-optimize mode
    if sys.version_info[:3] > (2,4,1) or not __debug__:
        # some Linux distributions don't include the profiling module (which
        # hotshot.stats depends on)
        try:
            import hotshot.stats
        except ImportError:
            pass
        else:
            suites.append(
                doctest.DocFileSuite(
                    'testrunner-profiling.txt',
                    setUp=setUp, tearDown=tearDown,
                    optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
                    checker = renormalizing.RENormalizing([
                        (re.compile(r'tests_profile[.]\S*[.]prof'),
                         'tests_profile.*.prof'),
                        ]),
                    )
                )
        try:
            import cProfile
            import pstats
        except ImportError:
            pass
        else:
            suites.append(
                doctest.DocFileSuite(
                    'testrunner-profiling-cprofiler.txt',
                    setUp=setUp, tearDown=tearDown,
                    optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
                    checker = renormalizing.RENormalizing([
                        (re.compile(r'tests_profile[.]\S*[.]prof'),
                         'tests_profile.*.prof'),
                        ]),
                    )
                )


    if hasattr(sys, 'gettotalrefcount'):
        suites.append(
            doctest.DocFileSuite(
            'testrunner-leaks.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
            checker = renormalizing.RENormalizing([
              (re.compile(r'\d+[.]\d\d\d seconds'), 'N.NNN seconds'),
              (re.compile(r'sys refcount=\d+ +change=\d+'),
               'sys refcount=NNNNNN change=NN'),
              (re.compile(r'sum detail refcount=\d+ +'),
               'sum detail refcount=NNNNNN '),
              (re.compile(r'total +\d+ +\d+'),
               'total               NNNN    NNNN'),
              (re.compile(r"^ +(int|type) +-?\d+ +-?\d+ *\n", re.M),
               ''),
              ]),

            )
        )
    else:
        suites.append(
            doctest.DocFileSuite(
            'testrunner-leaks-err.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
            checker=checker,
            )
        )

    try:
        import subunit
    except ImportError:
        suites.append(
            doctest.DocFileSuite(
                'testrunner-subunit-err.txt',
                setUp=setUp, tearDown=tearDown,
                optionflags=doctest.ELLIPSIS + doctest.NORMALIZE_WHITESPACE,
                checker=checker))
    else:
        suites.append(
            doctest.DocFileSuite(
                'testrunner-subunit.txt',
                setUp=setUp, tearDown=tearDown,
                optionflags=doctest.ELLIPSIS + doctest.NORMALIZE_WHITESPACE,
                checker=checker))
        if hasattr(sys, 'gettotalrefcount'):
            suites.append(
                doctest.DocFileSuite(
                    'testrunner-subunit-leaks.txt',
                    setUp=setUp, tearDown=tearDown,
                    optionflags=doctest.ELLIPSIS + doctest.NORMALIZE_WHITESPACE,
                    checker=checker))

    if sys.version_info[:3] >= (2,7,0):
        # Python 2.7 adds support for unittest.expectedFailure
        suites.append(doctest.DocFileSuite(
            'testrunner-unexpected-success.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
            checker=checker))

    return unittest.TestSuite(suites)
