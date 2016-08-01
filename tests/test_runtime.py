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
from statechart import InitialState, Metadata, State, Statechart, Transition


@pytest.fixture
def state():
    statechart = Statechart(name='statechart')
    initial_state = InitialState(statechart)
    next_state = State(name='next', context=statechart)
    Transition(initial_state, next_state)
    statechart.start()
    return next_state


class TestMetadata:
    def test_create_metadata(self):
        Metadata()

    def test_activate_inactive_state(self, state):
        metadata = Metadata()
        metadata.activate(state.context)
        metadata.activate(state)
        assert state in metadata.active_states

    def test_reactivate_active_state(self, state):
        metadata = Metadata()
        metadata.activate(state.context)
        metadata.activate(state)
        assert state in metadata.active_states
        metadata.activate(state)
        assert state in metadata.active_states

    def test_deactivate_active_state(self, state):
        metadata = Metadata()
        metadata.activate(state.context)
        metadata.activate(state)
        assert state in metadata.active_states
        metadata.deactivate(state)
        assert state not in metadata.active_states

    def test_deactivate_inactive_state(self, state):
        metadata = Metadata()
        metadata.activate(state.context)
        metadata.deactivate(state)
        assert state not in metadata.active_states

    def test_is_active_active_state(self, state):
        metadata = Metadata()
        metadata.activate(state.context)
        metadata.activate(state)
        assert metadata.is_active(state) is True

    def test_is_active_inactive_state(self, state):
        metadata = Metadata()
        metadata.activate(state.context)
        assert metadata.is_active(state) is False
