# -*- coding: utf-8 -*-

from os import path
from dolmen.template import TALTemplate, ITemplate
from dolmen.forms.base import _
from dolmen.forms.base.fields import Fields
from dolmen.forms.base.forms import FormCanvas
from dolmen.forms.base.forms import StandaloneForm, cloneFormData
from dolmen.forms.base.widgets import Widgets, getWidgetExtractor
from dolmen.forms.composed.form import SubFormBase

from dolmen.forms.table.select import SelectField
from dolmen.forms.table.actions import TableActions
from dolmen.forms.table import interfaces

from grokcore.component import baseclass, adapter, implementer
from zope.interface import implements, Interface


class TableFormCanvas(FormCanvas):
    """A form which is able to edit more than one content as a table.
    """
    baseclass()
    implements(interfaces.ITableFormCanvas)

    tableFields = Fields()
    tableActions = TableActions()
    emptyDescription = _(u"There are no items.")
    action_url = "."

    def __init__(self, context, request):
        super(TableFormCanvas, self).__init__(context, request)
        self.lines = []
        self.lineWidgets = []
 
    def updateLines(self, mark_selected=False):
        self.lines = []
        self.lineWidgets = []
        for position, item in enumerate(self.getItems()):
            prefix = u'%s.line-%d' % (self.prefix, position)
            form = cloneFormData(self, content=item, prefix=prefix)
            form.selected = False

            # Checkbox to select the line
            factory = getattr(self, 'selectFieldFactory', SelectField)
            selectedField = factory(identifier=position)

            if mark_selected:
                # Mark selected lines
                selectedExtractor = getWidgetExtractor(
                    selectedField, form, self.request)
                if selectedExtractor is not None:
                    value, error = selectedExtractor.extract()
                    if value:
                        form.selected = True

            lineWidget = Widgets(form=form, request=self.request)
            lineWidget.extend(selectedField)
            self.lines.append(form)
            self.lineWidgets.append(lineWidget)

    def updateActions(self):
        action, status = self.tableActions.process(self, self.request)
        if action is None:
            action, status = self.actions.process(self, self.request)
        return action, status

    def updateWidgets(self):
        self.updateLines()
        for widgets in self.lineWidgets:
            widgets.extend(self.tableFields)
        self.fieldWidgets.extend(self.fields)
        self.actionWidgets.extend(self.actions)
        self.actionWidgets.extend(self.tableActions)

        for widgets in self.lineWidgets:
            widgets.update()
        self.fieldWidgets.update()
        self.actionWidgets.update()

    def getItems(self):
        return self.context.values()


class TableForm(TableFormCanvas, StandaloneForm):
    """A full standalone TableForm.
    """
    baseclass()
    implements(interfaces.ITableForm)


class SubTableForm(SubFormBase, TableFormCanvas):
    """A table form which can be used in a composed form.
    """
    baseclass()
    implements(interfaces.ISubTableForm)


@implementer(ITemplate)
@adapter(interfaces.ISubTableForm, Interface)
def subtableform_template(component, request):
    filename = path.join(
        path.join(path.dirname(__file__), 'templates'), 'subtableform.pt')
    return TALTemplate(filename)
