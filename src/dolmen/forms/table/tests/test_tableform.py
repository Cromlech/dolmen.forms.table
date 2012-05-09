"""dolmen.forms.table tests
"""
# -*- coding: utf-8 -*-

import grokcore.component as grok

from cromlech.browser.testing import TestRequest
from cromlech.browser import IPublicationRoot
from dolmen.forms.base.fields import Field, Fields
from dolmen.forms.table import TableForm
from dolmen.forms.table.interfaces import ITableForm
from zope.interface import directlyProvides
from zope.interface.verify import verifyObject
from zope.testing.cleanup import cleanUp


class Person(object):
    def __init__(self, name, age):
        self.name = name
        self.age = age


content = {
    'Paul': Person(u'Gunther', 42),
    'Arthur': Person('Arthur', 24),
    'Merlin': Person('Merlin', 203412)}


fields = dict(
    age = Field('age'),
    name = Field('name'),
    )


class AdvancedForm(TableForm):
    ignoreContent = False
    ignoreRequest = True
    tableFields = Fields(*fields.values())


def setup_module(module):
    """Grok the modules !
    """
    grok.testing.grok("dolmen.location")
    grok.testing.grok("dolmen.forms.base")
    grok.testing.grok("dolmen.forms.table")


def teardown_module(module):
    """Undo grokking.
    """
    cleanUp()


def test_table_form():
    """Base tests : values and behavior.
    FIXME : this needs more tests.
    """
    request = TestRequest()
    form = TableForm(content, request)

    assert verifyObject(ITableForm, form)

    # We make sure getItems return the right amount of items.
    # This is used by ``updateLines`` to create widgets for all lines. Those
    # are have a line prefix:
    assert len(form.getItems()) == 3

    # We can proceed.
    form.update()
    form.updateForm()

    assert len(form.lines) == len(form.lineWidgets) == 3
    assert [line.prefix for line in form.lines] == [
        'form.line-0', 'form.line-1', 'form.line-2']

    # The result should contain HTML bas tags
    assert '<html>' in form.render()


def test_batching():
    """Base batching test. The Batcher is tested in ``dolmen.batch``.
    We simply need to make sure we have plugged it correctly and that
    it gets the right values out of the form.
    """
    request = TestRequest()
    form = TableForm(content, request)

    # The table can generate a batch out-of-the-box.
    # However, that capability has to be activated.
    form = TableForm(content, request)
    form.createBatch = True

    # @ testing conf.
    # To be able to compute the URL, we need to define a publication root
    directlyProvides(form, IPublicationRoot)

    # Now, we can test it:
    form.batchSize = 1
    form.update()
    assert form.batcher.size == 1
    assert form.batcher.url == 'http://localhost'


def test_widgets():
    """The table form generates rows of widgets to edit the lines' fields.
    We need to test that.
    FIXME: this needs real thorough tests.
    """
    request = TestRequest()
    form = AdvancedForm(content, request)
    form.update()
    form.updateForm()
    result = form.render()

    assert ('Gunther' in result and '42' in result)
    assert ('Merlin' in result and '24' in result)
    assert ('Arthur' in result and '203412' in result)
