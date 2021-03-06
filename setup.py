# -*- coding: utf-8 -*-

from os.path import join
from setuptools import setup, find_packages


name = 'dolmen.forms.table'
version = '2.2.1'
readme = open(join('src', 'dolmen', 'forms', 'table', 'README.txt')).read()
history = open(join('docs', 'HISTORY.txt')).read()

install_requires = [
    'cromlech.browser >= 0.5',
    'cromlech.i18n',
    'dolmen.batch >= 0.2',
    'dolmen.forms.base >= 2.4',
    'dolmen.forms.composed',
    'dolmen.template',
    'grokcore.component',
    'setuptools',
    'zope.component',
    'zope.interface',
    'zope.location',
    ]

tests_require = [
    'cromlech.browser [test]',
    'dolmen.location >= 0.2',
    'zope.testing',
    ]

setup(name=name,
      version=version,
      description="Form as table, to edit more than one content at a time",
      long_description=readme + '\n\n' + history,
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='Dolmen form table',
      author='The Dolmen Team',
      author_email='dolmen@list.dolmen-project.org',
      url='http://pypi.python.org/pypi/dolmen.forms.table',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['dolmen', 'dolmen.forms'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      )
