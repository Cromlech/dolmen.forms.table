# -*- coding: utf-8 -*-

from zope import interface
from dolmen.forms.base.interfaces import IFormCanvas, IForm
from dolmen.forms.composed.interfaces import ISubForm


class ITableFormCanvas(IFormCanvas):
    """Base form behavior for forms working on more than one content
    at a time.
    """

    lines = interface.Attribute(u"Widgets lines")

    def updateLines():
        """Prepare widgets and forms for each lines.
        """

    def getItems():
        """Return the list of contents.
        """


class ITableForm(IForm, ITableFormCanvas):
    """A form which is able to work on more than one item at a time.
    """


class ISubTableForm(ISubForm, ITableFormCanvas):
    """A table form that can be used in a composed form.
    """
