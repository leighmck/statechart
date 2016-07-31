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


class Guard(metaclass=abc.ABCMeta):
    """
    A guard is a boolean expression that is attached to a transition as a
    fine-grained control over its firing. The guard is evaluated when an event
    instance is dispatched by the state machine. If the guard is true at that
    time, the transition is enabled, otherwise, it is disabled.

    Guards should be pure expressions without side effects.

    Example:
        Create a derived class of Guard:

        class GreaterThanZero(Guard):
            def check(self, event):
                return event.value > 0

        Add guard to transition:

        Transition(start=a, end=b, event=my_event, guard=GreaterThanZero())

        Fire the event. If the state has a transition that :
        statechart.dispatch(Event(name='my event', value=10))
    """

    @abc.abstractmethod
    def check(self, metadata, event):
        """
        Called by the transition, override for specific behaviour

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): Transition event trigger.

        Note:
            Checking a guard should not have any side effects, therefore don't
            mutate event parameter data.
            The evaluation must always be a boolean expression.

        Returns:
            Boolean result of expression.

        Raises:
            Not implemented error for abstract class.
        """
        raise NotImplementedError


class CallGuard(Guard):
    """
    Generic guard configured with a callback function, checked when the Transition is fired.

    Note:
        The callback function must be exception safe and support args for the statechart metadata
        and transition event trigger.

        e.g. def callback(self, metadata, event):
    """

    def __init__(self, callback):
        self._callback = callback

    def check(self, metadata, event):
        """
        Called by the transition.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): Transition event trigger.

        Returns:
            The result returned by the callback function.
        """
        return bool(self._callback(metadata=metadata, event=event))


class ElseGuard(Guard):
    """
    Simple 'else' guard condition which always returns True when checked.

    Useful guard for outgoing transitions from Choice Pseudostates to ensure there is at least
    one path that can be executed.
    """

    def check(self, metadata, event):
        """
        Called by the transition.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): Transition event trigger.

        Returns:
            True.
        """
        return True


class EqualGuard(Guard):
    """
    Check if the two inputs 'a' and 'b' are equal.

    Args:
        a: First input.
        b: Second input.
    """

    def __init__(self, a, b):
        self._a = a
        self._b = b

    def check(self, metadata, event):
        """
        Called by the transition.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): Transition event trigger.

        Returns:
            The result of the equality check between 'a' and 'b'.
        """
        return self._a == self._b
