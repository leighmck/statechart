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

from statechart import (CompositeState, Event, InitialState, State, Statechart, Transition)


class TopState(CompositeState):
    def __init__(self, name, context):
        CompositeState.__init__(self, name=name, context=context)
        self.scope['top_int'] = 1
        self.scope['top_str'] = 'top'


class MiddleState(CompositeState):
    def __init__(self, name, context):
        CompositeState.__init__(self, name=name, context=context)
        self.scope['middle_int'] = 5
        self.scope['middle_str'] = 'middle'


class BottomStateA(State):
    def __init__(self, name, context):
        State.__init__(self, name=name, context=context)
        self.scope['bottom_a_int'] = 8
        self.scope['bottom_a_str'] = 'bottom a'


class BottomStateB(State):
    def __init__(self, name, context):
        State.__init__(self, name=name, context=context)
        self.scope['bottom_b_int'] = 9
        self.scope['bottom_b_str'] = 'bottom b'

    def entry(self, param):
        super().entry(param=param)
        self.scope['top_int'] = 2


class TestScope:
    def test_scope(self):
        """
        statechart:

        statechart_init
               |
        *** top ***********************************************
        *                                                     *
        *  top_init                                           *
        *      |                                              *
        *  *** middle **************************************  *
        *  *                                               *  *
        *  *  middle_init                                  *  *
        *  *        |                                      *  *
        *  *  *** bottom_a ***           *** bottom_b ***  *  *
        *  *  *              * -- AB --> *              *  *  *
        *  *  ****************           ****************  *  *
        *  *                                               *  *
        *  *************************************************  *
        *                                                     *
        *******************************************************
        """
        statechart = Statechart(name='statechart', param=0)
        statechart_init = InitialState(name='statechart_init',
                                       context=statechart)

        top_state = TopState(name='top', context=statechart)
        top_init = InitialState(name='top_init', context=top_state)

        middle_state = MiddleState(name='middle', context=top_state)
        middle_init = InitialState(name='middle_init', context=middle_state)

        bottom_a = BottomStateA(name='bottom_a', context=middle_state)
        bottom_b = BottomStateB(name='bottom_b', context=middle_state)

        AB = Event(name='AB', param=None)

        Transition(name='statechart_default', start=statechart_init,
                   end=top_state)
        Transition('top_default', start=top_init,
                   end=middle_state)
        Transition('middle_default', start=middle_init,
                   end=bottom_a)
        Transition(name='AB', start=bottom_a, end=bottom_b, event=AB)

        statechart.start()

        assert statechart.metadata.is_active(bottom_a)
        assert dict(top_state.scope) == {
            'top_int': 1,
            'top_str': 'top',
        }

        # Assert the bottom a scope includes all parent scopes as well as it's own.
        assert bottom_a.scope == {
            'top_int': 1,
            'top_str': 'top',
            'middle_int': 5,
            'middle_str': 'middle',
            'bottom_a_int': 8,
            'bottom_a_str': 'bottom a',
        }

        # Dispatch event AB to trigger a state transition between
        # bottom states A and B.
        # The entry action of bottom state B should assign a value of 2
        # to the top level statechart to verify the rootscope is
        # mutable.
        statechart.dispatch(event=AB)

        assert statechart.metadata.is_active(bottom_b)

        # Assert the top state's scope was mutated by the bottom_b entry action.
        assert top_state.scope == {
            'top_int': 2,
            'top_str': 'top',
        }

        # Assert the bottom b scope includes all parent scopes as well as it's own.
        # Also ensure there is no carry-over from deactivated state a.
        assert bottom_b.scope == {
            'top_int': 2,
            'top_str': 'top',
            'middle_int': 5,
            'middle_str': 'middle',
            'bottom_b_int': 9,
            'bottom_b_str': 'bottom b',
        }
