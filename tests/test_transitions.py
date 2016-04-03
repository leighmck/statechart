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

import pytest
from statechart import (Action, Event, State, InitialState, InternalTransition,
                        Statechart, Transition)


class ActionSpy(Action):
    def __init__(self):
        self.executed = False

    def execute(self, param):
        self.executed = True


class MockParam(object):
    def __init__(self):
        self.path = str()


@pytest.fixture
def empty_statechart():
    statechart = Statechart(name='statechart', param=0)
    return statechart


class TestTransition:
    def test_create_transition(self, empty_statechart):
        initial_state = InitialState(name='initial', context=empty_statechart)
        next_state = State(name='next', context=empty_statechart)
        transition = Transition(name='name', start=initial_state,
                                end=next_state)

        # The transition should be added to the initial state's list of
        # outgoing transitions
        assert transition in initial_state.transitions

        # When executed, the transition should be setup to deactivate the
        # initial state and to activate the next state
        assert initial_state in transition.deactivate
        assert next_state in transition.activate

    def test_create_cyclic_transition(self, empty_statechart):
        next_state = State(name='next', context=empty_statechart)
        transition = Transition(name='name', start=next_state,
                                end=next_state)

        # The transition should be added to the initial state's list of
        # outgoing transitions.
        assert transition in next_state.transitions

        # When executed, the transition should be setup to deactivate the
        # next state and to re-activate it.
        assert next_state in transition.deactivate
        assert next_state in transition.activate


class TestInternalTransition:
    def test_execute(self, empty_statechart):
        initial_state = InitialState(name='initial', context=empty_statechart)
        entry_action = ActionSpy()
        do_action = ActionSpy()
        exit_action = ActionSpy()
        default_state = State(name='next', context=empty_statechart,
                              entry=entry_action, do=do_action,
                              exit=exit_action)
        Transition(name='name', start=initial_state,
                   end=default_state)

        internal_event = Event(name='internal-event', param='my-param')
        internal_action = ActionSpy()
        InternalTransition(name='internal',
                           state=default_state,
                           event=internal_event,
                           guard=None,
                           action=internal_action)
        empty_statechart.start()

        assert empty_statechart.metadata.is_active(default_state)
        assert entry_action.executed is True
        assert do_action.executed is True
        assert exit_action.executed is False

        # Ensure we don't leave and re-enter the default state after triggering
        # the internal transition.
        entry_action.executed = False
        do_action.executed = False

        empty_statechart.dispatch(internal_event)

        assert entry_action.executed is False
        assert do_action.executed is False
        assert exit_action.executed is False

        assert internal_action.executed is True
