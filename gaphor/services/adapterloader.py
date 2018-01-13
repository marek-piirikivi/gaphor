#!/usr/bin/env python

# Copyright (C) 2007-2017 Arjan Molenaar <gaphor@gmail.com>
#                         Artur Wroblewski <wrobell@pld-linux.org>
#                         Dan Yeaw <dan@yeaw.me>
#
# This file is part of Gaphor.
#
# Gaphor is free software: you can redistribute it and/or modify it under the
# terms of the GNU Library General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# Gaphor is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License 
# more details.
#
# You should have received a copy of the GNU Library General Public 
# along with Gaphor.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import
from zope import interface
from gaphor.interfaces import IService


class AdapterLoader(object):
    """
    Initiate adapters from the gaphor.adapters module.
    """

    interface.implements(IService)

    def init(self, app):
        import gaphor.adapters
        import gaphor.adapters.connectors
        import gaphor.adapters.editors
        import gaphor.adapters.grouping
        import gaphor.adapters.propertypages
        import gaphor.adapters.states

    def shutdown(self):
        pass


# vim:sw=4:et:ai
