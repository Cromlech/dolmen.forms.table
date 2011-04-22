# -*- coding: utf-8 -*-

from os import path
from dolmen.template import TALTemplate
from dolmen.forms.base.fields import Field
from dolmen.forms.base.widgets import FieldWidget, WidgetExtractor
from grokcore.component import adapts

PATH = path.join(path.dirname(__file__), 'templates')


class SelectField(Field):
    # This field is always in input and have a different prefix
    mode = 'input'
    prefix = 'select'
    ignoreContent = True
    ignoreRequest = False


class SelectFieldWidget(FieldWidget):
    adapts(SelectField, None, None)
    template = TALTemplate(path.join(PATH, 'selectfield.pt'))

    def htmlClass(self):
        cls = ['field', '-'.join([self.form.parent.htmlId(), 'select'])]
        return ' '.join(cls)


class SelectFieldExtractor(WidgetExtractor):
    adapts(SelectField, None, None)

    def extract(self):
        value, error = WidgetExtractor.extract(self)
        if value == 'selected':
            return value, None
        return None, None
