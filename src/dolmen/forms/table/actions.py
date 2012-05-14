# -*- coding: utf-8 -*-

from dolmen.forms.base import _
from dolmen.forms.base.markers import (
    NO_VALUE, SUCCESS, FAILURE, NOTHING_DONE, getValue)
from dolmen.forms.base.actions import Actions
from dolmen.forms.base.errors import Error
from dolmen.forms.base.interfaces import IWidgetExtractor, ActionError
from dolmen.forms.table import interfaces
from zope.component import getMultiAdapter


def verify_post(action, form, request):
    isPostOnly = getValue(action, 'postOnly', form)
    if isPostOnly and request.method != 'POST':
        form.errors.append(
            Error('This form was not submitted properly.',
                  form.prefix))
        return False
    else:
        return True


def merge_errors(line, form):
    """Merge global line errors to form errors"""
    target = form.errors
    add_marker = False
    for error in line.errors:
        if error.identifier == line.prefix:
            target.append(Error(error.title, form.prefix))
            add_marker = True
    if add_marker:
        line.errors.append(Error(' ', 'select'))


def extract_all_data(form):
    parent = form.parent
    data, errors =  form.extractData(parent.tableFields)
    data_, errors_ = parent.extractData(parent.fields)
    data.update(data_)
    errors.extend(errors_)
    return data, errors


class TableActions(Actions):
    """Actions that can be applied on a table.

    Actions are applied for each selected table line.
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
                if not verify_post(action, form, request):
                    return action, FAILURE
                if not ready:
                    form.updateLines(mark_selected=True)
                    ready = True
                # first validate
                got_error = False
                for line in form.lines:
                    if not line.selected:
                        continue
                    one_selected = True
                    try:
                        got_error |=  not action.validate(line)
                    except ActionError, e:
                        got_error = True
                        line.errors.append(
                            Error(unicode(e), identifier=line.prefix))
                    if line.errors:
                        merge_errors(line, form)

                if not one_selected:
                    form.errors.append(
                        Error(_(u"You didn't select any item!"), form.prefix))
                    got_error = True

                if got_error:
                    return action, FAILURE

                # then compute
                for line in form.lines:
                    if not line.selected:
                        continue
                    try:
                        status = action(line)
                        got_error |= status != SUCCESS
                    except ActionError, e:
                        form.errors.append(Error(e.args[0], line.prefix))
                        got_error = True
                    if line.errors:
                        merge_errors(line, form)
                return action, SUCCESS if not got_error else FAILURE
        return None, NOTHING_DONE
