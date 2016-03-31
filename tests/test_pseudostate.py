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

from statechart import InitialState, State, Statechart, Transition


class TestInitialState:
    def test_create_initial_state(self):
        startchart = Statechart(name='statecart', param=0)
        InitialState(name='initial', context=startchart)

    def test_activate_initial_state(self):
        startchart = Statechart(name='test', param=0)
        initial_state = InitialState(name='initial', context=startchart)
        default_state = State(name='default', context=startchart)
        Transition('default', start=initial_state,
                   end=default_state)
        startchart.start()

        initial_state.activate(metadata=startchart.metadata, param=0)
        assert startchart.metadata.is_active(state=default_state)
