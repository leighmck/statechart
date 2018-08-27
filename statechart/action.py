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

import abc


class Action(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def execute(self, event):
        """
        Called by the transition, override for specific behaviour.

        Args:
            event (Event): The event which triggered this action.

        Raises:
            Not implemented error for abstract class.
        """
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)


class CallAction(Action):
    """
    Generic action configured with a callback function, executed when the Transition is fired.

    Note:
        The callback function must be exception safe and support args for the statechart
        transition event trigger.

        e.g. def callback(self, event):
    """

    def __init__(self, callback):
        self.callback = callback

    def execute(self, event):
        """
        Called by the transition, executes the callback function, passing the statechart
        transition event trigger.

        Args:
            event (Event): The event which triggered this action.
        """
        self.callback(event=event)
