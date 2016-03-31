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
from statechart import State, InitialState, Statechart, Transition


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
