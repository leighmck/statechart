# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Leigh McKenzie
# All rights reserved.
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import logging

class Event:
    """
    An event is a specification of a type of observable occurrence. The
    occurrence that generates an event instance is assumed to take place at an
    instant in time with no duration.

    :param name: An identifier for the event.
    :param param: The parameter for this event.
    """

    def __init__(self, name, param):
        self.name = name
        self.param = param
        self._logger = logging.getLogger(__name__)

    def __eq__(self, event):
        """
        Determine if an event is equal to this event by comparing names.

        :param event: Event to compare.
        :return: True if events are equal.
        """
        if event is None:
            return False

        return self.name == event.name

    def __ne__(self, event):
        """
        Determine if an event is not equal to this event by comparing names.

        :param event:
        :return: True if events are not equal.
        """
        return not self.__eq__(event)

    def __str__(self):
        """
        Returns a string representation the event.
        :return: "Event: {'name'}" including the instance's name.
        """
        return "Event: {name}".format(name=str(self.name))
