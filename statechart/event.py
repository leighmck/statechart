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

    Example:
        Create an instance of an event:
        my_event = Event(name='my event')

        Add the event trigger to a transition:
        Transition(start=a, end=b, event=my_event)

        Fire the event:
        statechart.dispatch(event=my_event)

        If the current state has an outgoing transition associated
        with the event, it may be fired if the guard condition allows.

    Args:
        name (str): An identifier for the event.
        data Optional[dict]: Optional data dict.
    """

    def __init__(self, name, data=None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.data = data or {}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self):
        return 'Event(name="%s", data=%r)' % (self.name, self.data)
