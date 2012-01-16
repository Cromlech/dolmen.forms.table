# -*- coding: utf-8 -*-

import operator
from os import path

from cromlech.i18n import ILanguage
from grokcore.component import baseclass, adapter, implementer
from zope.interface import implements, Interface
from zope.location import ILocation, LocationProxy

from dolmen.batch import Batcher
from dolmen.template import TALTemplate, ITemplate
from dolmen.forms.base import DISPLAY, _
from dolmen.forms.base import Fields, Actions, Widgets
from dolmen.forms.base.forms import FormData, FormCanvas
from dolmen.forms.base.forms import StandaloneForm, cloneFormData
from dolmen.forms.base.widgets import Widgets, getWidgetExtractor
from dolmen.forms.composed.form import SubFormBase
from dolmen.forms.table.select import SelectField
from dolmen.forms.table.actions import TableActions
from dolmen.forms.table import interfaces


TEMPLATES = path.join(path.dirname(__file__), 'templates')


def get_template(filename):
    return TALTemplate(path.join(TEMPLATES, filename))


class BaseTable(FormData):
    """Action-less table component.
    """
    mode = DISPLAY
    fields = Fields()
    template = get_template('table.pt')

    label = u""
    description = u""

    css_id = None
    css_class = None

    batchSize = 10
    createBatch = False

    ignoreContent = False
    ignoreRequest = True
    _updated = False

    def __init__(self, context, request):
        super(BaseTable, self).__init__(context, request)
        self.fieldWidgets = Widgets(form=self, request=self.request)
        self.lines = []
        self.lineWidgets = []
        self.batcher = None

    @property
    def target_language(self):
        return ILanguage(self.request, None)

    @property
    def title(self):
        return u"<h1>%s</h1>" % (
            getattr(self.context, 'title', None) or self.context.__name__)

    def getItems(self):
        return self.context.values()

    def items(self):
        if self.createBatch:
            self.batcher.update(self.getItems())
            return self.batcher.batch
        return self.getItems()

    def namespace(self):
        namespace = {}
        namespace['view'] = namespace['table'] = self
        namespace['lines'] = self.lineWidgets
        namespace['fields'] = self.fields
        return namespace

    def updateLines(self):
        self.lines = []
        self.lineWidgets = []
        for position, item in enumerate(self.items()):
            prefix = u'%s.line-%d' % (self.prefix, position)
            form = cloneFormData(self, content=item, prefix=prefix)
            lineWidget = Widgets(form=form, request=self.request)
            self.lines.append(form)
            self.lineWidgets.append(lineWidget)

    def updateWidgets(self):
        for widgets in self.lineWidgets:
            widgets.extend(self.fields)

        for widgets in self.lineWidgets:
            widgets.update()

        self.fieldWidgets.update()

    def update(self, *args, **kwargs):
        if self._updated is False:
            self.updateLines()
            self.updateWidgets()
            if self.createBatch:
                content = self.getContentData().getContent()
                if not ILocation.providedBy(content):
                    content = LocationProxy(content)
                    content.__parent__ = self
                    content.__name__ = ''
                self.batcher = Batcher(
                    content, self.request, self.prefix, size=self.batchSize)
                self.batcher.update(self.lines)
            self._updated = True

    def render(self, *args, **kwargs):
        res = self.template.render(self, target_language=self.target_language) 
        return u"<html><body>%s</body><html>" % res


class TableFormCanvas(BaseTable):
    """A form which is able to edit more than one content as a table.
    """
    implements(interfaces.ITableFormCanvas)
    template = get_template('tablecanvas.pt')

    action_url = ""

    actions = Actions()
    tableFields = Fields()
    tableActions = TableActions()
    emptyDescription = _(u"There are no items.")

    def __init__(self, context, request):
        super(TableFormCanvas, self).__init__(context, request)
        self.lines = []
        self.lineWidgets = []
        self.actionWidgets = Widgets(form=self, request=self.request)

    def createSelectedField(self, item):
        """Return a field to select the line.
        """
        return SelectField(identifier='select')

    def haveRequiredFields(self):
        return reduce(
            operator.or_,
            [False] + map(operator.attrgetter('required'), self.fields))

    def updateLines(self, mark_selected=False):
        self.lines = []
        self.lineWidgets = []
        self.batching = None
        items = self.getItems()
        for position, item in enumerate(items):
            prefix = '%s.line-%d' % (self.prefix, position)
            form = cloneFormData(self, content=item, prefix=prefix)
            form.selected = False

            # Checkbox to select the line
            form.selectedField = self.createSelectedField(item)

            if mark_selected:
                # Mark selected lines
                selectedExtractor = getWidgetExtractor(
                    form.selectedField, form, self.request)
                if selectedExtractor is not None:
                    value, error = selectedExtractor.extract()
                    if value:
                        form.selected = True

            lineWidget = Widgets(form=form, request=self.request)
            lineWidget.extend(form.selectedField)
            self.lines.append(form)
            self.lineWidgets.append(lineWidget)

    def updateActions(self):
        form, action, status = self.tableActions.process(self, self.request)
        if action is None:
            form, action, status = self.actions.process(self, self.request)
        return form, action, status

    def updateWidgets(self):
        self.updateLines()
        for widgets in self.lineWidgets:
            widgets.extend(self.tableFields)
        self.fieldWidgets.extend(self.fields)
        self.actionWidgets.extend(self.tableActions)
        self.actionWidgets.extend(self.actions)

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

    def update(self, *args, **kwargs):
        TableFormCanvas.update(self, *args, **kwargs)
        StandaloneForm.update(self, *args, **kwargs)

    def namespace(self):
        ns = StandaloneForm.namespace(self)
        ns.update(TableFormCanvas.namespace(self))
        return ns


class SubTableForm(SubFormBase, TableFormCanvas):
    """A table form which can be used in a composed form.
    """
    baseclass()
    implements(interfaces.ISubTableForm)
    template = get_template('subtableform.pt')

    def update(self, *args, **kwargs):
        SubFormBase.update(self, *args, **kwargs)
        TableFormCanvas.update(self, *args, **kwargs)

    def namespace(self):
        ns = SubFormBase.namespace(self)
        ns.update(TableFormCanvas.namespace(self))
        return ns
