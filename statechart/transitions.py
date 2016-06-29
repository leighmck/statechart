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
from statechart import Statechart


class Transition:
    """
    A transition is a directed relationship between a source state and a target
    state. It may be part of a compound transition, which takes the state
    machine from one state configuration to another, representing the complete
    response of the state machine to a particular event instance.

    :param name: An identifier for the Transition.
    :param start: The originating state (or pseudostate) of the transition.
    :param end: The target state (or pseudostate) that is reached when the
        transition is executed.
    :param event: The event that fires the transition.
    :param guard: A boolean predicate that  must be true for the transition to
        be fired. It is evaluated at the time the event is dispatched.
    :param action: An optional procedure to be performed when the transition
       fires.
    """

    def __init__(self, name, start, end, event=None, guard=None, action=None):
        self.name = name
        self.start = start
        self.end = end
        self.event = event
        self.guard = guard
        self.action = action

        self._logger = logging.getLogger(__name__)

        """ Used to store the states that will get activated """
        self.activate = list()

        """ Used to store the states that will get de-activated """
        self.deactivate = list()

        self._calculate_state_set(start, end)

        start.add_transition(self)

    def _calculate_state_set(self, start, end):
        start_states = list()
        end_states = list()

        """ Recursively get all the context start states """
        s = start
        while s is not None:
            start_states.insert(0, s)
            context = s.context
            if context and not isinstance(context, Statechart):
                s = context
            else:
                s = None

        """ Recursively get all the context end states """
        e = end
        while e is not None:
            end_states.insert(0, e)
            context = e.context
            if context and not isinstance(context, Statechart):
                e = context
            else:
                e = None

        """ Get the Least Common Ancestor (LCA) of the start and end states """
        min_state_count = min(len(start_states), len(end_states))
        lca = min_state_count - 1

        if start is not end:
            lca = 0
            while lca < min_state_count:
                if start_states[lca] is not end_states[lca]:
                    break
                lca += 1

        """ Starting from the LCA get the states that will be deactivated """
        i = lca
        while i < len(start_states):
            self.deactivate.insert(0, start_states[i])
            i += 1

        """ Starting from the LCA get the states that will be activated """
        i = lca
        while i < len(end_states):
            self.activate.append(end_states[i])
            i += 1

    def execute(self, metadata, event, param):
        """
        Attempt to execute the transition.
        Evaluate if the transition is allowed by checking the guard condition.
        If the transition is allowed, deactivate source states, perform
        transition action and activate all target states.

        :param metadata:
        :param event:
        :param param:
        :return: True if the transition was executed.
        """
        self._logger.info('execute %s', self.name)

        if self.event and event is None:
            self._logger.info('default transition not activated')
            return False

        if self.event and self.event != event:
            self._logger.info('transition not triggered by event %s', event)
            return False

        if self.guard and not self.guard.check(metadata, param):
            self._logger.info('transition blocked by guard condition %s', event)
            return False

        metadata.event = event
        metadata.transition = self

        for state in self.deactivate:
            state.deactivate(metadata, param)

        if self.action:
            self.action.execute(param)

        for state in self.activate:
            state.activate(metadata, param)

        metadata.transition = None
        metadata.event = None

        return True


class InternalTransition(Transition):
    """
    A transition that executes without exiting or re-entering the state in
    which it is defined. This is true even if the state machine is in a nested
    state within this state.

    :param name: An identifier for the Transition.
    :param state: The containing state.
    :param event: The event that fires the transition.
    :param guard: A boolean predicate that  must be true for the transition to
        be fired. It is evaluated at the time the event is dispatched.
    :param action: An optional procedure to be performed when the transition
       fires.
    """

    def __init__(self, name, state, event, guard, action):
        Transition.__init__(self, name=name, start=state, end=state,
                            event=event, guard=guard, action=action)
        self.deactivate.clear()
        self.activate.clear()

    def execute(self, metadata, event, param):
        """
        Attempt to execute the transition.
        Evaluate if the transition is allowed by checking the guard condition.
        If the transition is allowed perform transition action.

        :param metadata: The metadata data object.
        :param event: The event that fires the transition.
        :param param: The parameter for this transition.
        :return: True if the transition was executed.
        """
        if self.event and event != self.event:
            return False

        if self.guard and not self.guard.check(metadata, param):
            return False

        if self.action:
            self.action.execute(param)

        return True
