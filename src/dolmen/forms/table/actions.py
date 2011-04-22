# -*- coding: utf-8 -*-

from dolmen.forms.base import _
from dolmen.forms.base.markers import NO_VALUE, SUCCESS, FAILURE, NOTHING_DONE
from dolmen.forms.base.actions import Actions
from dolmen.forms.base.errors import Error
from dolmen.forms.base.interfaces import IWidgetExtractor, ActionError
from dolmen.forms.table import interfaces
from zope.component import getMultiAdapter


class TableActions(Actions):
    """Actions that can be applied on a table.
    """

    def process(self, form, request):
        assert interfaces.ITableFormCanvas.providedBy(form)
        one_selected = False
        ready = False

        for action in self:
            extractor = getMultiAdapter(
                (action, form, request), IWidgetExtractor)
            value, error = extractor.extract()
            if value is not NO_VALUE:
                if not ready:
                    form.updateLines(mark_selected=True)
                    ready = True
                for line in form.lines:
                    if not line.selected:
                        continue
                    one_selected = True
                    try:
                        if action.validate(line):
                            content = line.getContentData().getContent()
                            action(form, content, line)
                    except ActionError, e:
                        line.errors.append(Error(e.args[0], line.prefix))
                if not one_selected:
                    form.errors.append(
                        Error(_(u"You didn't select any item!"), None))
                    return action, FAILURE
                return action, SUCCESS
        return None, NOTHING_DONE
