from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library

standard_library.install_aliases()
import datetime

import click


class KeyValueType(click.ParamType):
    name = 'key=value'

    def convert(self, value, param, ctx):
        try:
            k, v = value.split('=', 1)
            return k.strip(), v.strip()
        except ValueError:
            self.fail(_('"%s" is not a valid key/value pair') % value, param, ctx)


class DateType(click.ParamType):
    name = 'key=value'

    def convert(self, value, param, ctx):
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            self.fail(_('"%s" is not a valid date') % value, param, ctx)


class ListType(click.ParamType):
    name = 'list'

    def convert(self, value, param, ctx):
        return value.split(',')


keyvalue = KeyValueType()
date = DateType()
list = ListType()
