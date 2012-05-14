# -*- coding: utf-8 -*-

import operator
from os import path

from cromlech.i18n import ILanguage
from cromlech.browser import HTMLWrapper
from grokcore.component import baseclass
from zope.interface import implements
from zope.location import ILocation, LocationProxy

from dolmen.batch import Batcher
from dolmen.template import TALTemplate
from dolmen.forms.base import DISPLAY, _
from dolmen.forms.base import Fields, Actions, Widgets
from dolmen.forms.base import FormData, cloneFormData, SUCCESS
from dolmen.forms.base.widgets import getWidgetExtractor
from dolmen.forms.base.components import StandaloneForm
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
        return (u"<h1>%s</h1>" % self.label) or ''

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
        namespace['table_fields'] = self.tableFields
        namespace['lines'] = self.lineWidgets
        namespace['fields'] = self.fieldWidgets
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
        pass

    def update_batch(self):
        if self.createBatch:
            content = self.getContentData().getContent()
            if not ILocation.providedBy(content):
                content = LocationProxy(content)
                content.__parent__ = self
                content.__name__ = ''
            self.batcher = Batcher(
                content, self.request, self.prefix, size=self.batchSize)
            self.batcher.update(self.lines)

    def updateForm(self, *args, **kwargs):
        if self._updated is False:
            self.updateLines()
            self.updateWidgets()
            self.update_batch()
            self._updated = True

    def render(self, *args, **kwargs):
        html = HTMLWrapper()
        res = self.template.render(self, target_language=self.target_language)
        return html.render(content=res.encode('utf-8'))


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

    @property
    def tableDataManager(self):
        """By default tableDataManager is dataManager

        but you may override it"""
        return self.dataManager

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

    def mark_selected(self, line):
        # Mark selected lines
        selectedExtractor = getWidgetExtractor(
            line.selectedField, line, self.request)
        if selectedExtractor is not None:
            value, error = selectedExtractor.extract()
            if value:
                line.selected = True

    def generate_line_form(self, content, prefix):
        """
        Generate form for a specific line, using content.
        """
        form = cloneFormData(self, content=content, prefix=prefix)
        # TODO : if cloneFormData would copy dataValidators
        # and accept kwargs to override eg. dataManager
        # this would not happen, fix it in forms.base!
        form.dataManager = self.tableDataManager
        form.dataValidators = self.dataValidators
        form.setContentData(content)
        # context is content so that vocabularies work !
        form.context = content
        form.__parent__ = self
        return form

    def updateLines(self, mark_selected=False):
        self.lines = []
        self.lineWidgets = []
        self.batching = None
        items = self.getItems()
        for position, item in enumerate(items):
            # each line is like a form
            prefix = '%s.line-%d' % (self.prefix, position)
            form = self.generate_line_form(content=item, prefix=prefix)
            form.selected = False

            # Checkbox to select the line
            form.selectedField = self.createSelectedField(item)

            if mark_selected:
                self.mark_selected(form)

            lineWidget = Widgets(form=form, request=self.request)
            lineWidget.extend(form.selectedField)
            self.lines.append(form)
            self.lineWidgets.append(lineWidget)

    def updateActions(self):
        action, result = self.tableActions.process(self, self.request)
        if action is None:
            action, result = self.actions.process(self, self.request)
        return action, result

    def updateWidgets(self):
        for widgets in self.lineWidgets:
            widgets.extend(self.tableFields)
        self.fieldWidgets.extend(self.fields)
        self.actionWidgets.extend(self.tableActions)
        self.actionWidgets.extend(self.actions)

        for widgets in self.lineWidgets:
            widgets.update()
        self.fieldWidgets.update()
        self.actionWidgets.update()

    def updateForm(self, *args, **kwargs):
        if self._updated is False:
            self.updateLines()
            action, result = self.updateActions()
            if action and result is SUCCESS:
                self.ignoreRequest = True  # line number may have changed !
                # refresh lines
                self.updateLines()
            self.updateWidgets()
            self.update_batch()
            self._updated = True

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
