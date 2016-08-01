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

from statechart import (ChoiceState, CompositeState, ElseGuard, Event, Guard, InitialState,
                        Metadata, ShallowHistoryState, State, Statechart, Transition)


class TestInitialState:
    def test_create_initial_state(self):
        startchart = Statechart(name='statechart')
        InitialState(startchart)

    def test_activate_initial_state(self):
        startchart = Statechart(name='statechart')
        initial_state = InitialState(startchart)
        default_state = State(name='default', context=startchart)
        Transition(start=initial_state, end=default_state)
        startchart.start()

        initial_state.activate(metadata=startchart._metadata, event=None)
        assert startchart.is_active('default')

    def test_missing_transition_from_initial_state(self):
        startchart = Statechart(name='statechart')
        InitialState(startchart)

        with pytest.raises(RuntimeError):
            startchart.start()

    def test_multiple_transitions_from_initial_state(self):
        startchart = Statechart(name='statechart')
        initial_state = InitialState(startchart)
        default_state = State(name='default', context=startchart)

        Transition(start=initial_state, end=default_state)
        with pytest.raises(RuntimeError):
            Transition(start=initial_state, end=default_state)

    def test_transition_from_initial_state_with_event_trigger(self):
        startchart = Statechart(name='statechart')
        initial_state = InitialState(startchart)
        default_state = State(name='default', context=startchart)

        with pytest.raises(RuntimeError):
            Transition(start=initial_state, end=default_state, event=Event('event'))

    def test_transition_from_initial_state_with_guard_condition(self):
        class MyGuard(Guard):
            def check(self, metadata, event):
                return False

        startchart = Statechart(name='statechart')
        initial_state = InitialState(startchart)
        default_state = State(name='default', context=startchart)

        with pytest.raises(RuntimeError):
            Transition(start=initial_state, end=default_state, event=None, guard=MyGuard())


class TestShallowHistoryState:
    def test_create_shallow_history_state(self):
        startchart = Statechart(name='statechart')
        composite_state = CompositeState(name='composite', context=startchart)
        ShallowHistoryState(composite_state)

    def test_cannot_create_multiple_shallow_history_states(self):
        startchart = Statechart(name='statechart')
        composite_state = CompositeState(name='composite', context=startchart)

        ShallowHistoryState(composite_state)

        with pytest.raises(RuntimeError):
            ShallowHistoryState(composite_state)

    def test_activate_shallow_history_state(self):
        """
        statechart:

        statechart_init
                  |
        *** csa **********************          *** csb *************
        *                            *          *                   *
        *  csa_init-csa_hist         *          *  csb_init         *
        *              |             *  --J-->  *     |             *
        *              A  --I-->  B  *  <--K--  *     C  --L-->  D  *
        *                            *          *                   *
        ******************************          *********************
        """

        # Top level states
        statechart = Statechart(name='statechart')
        csa = CompositeState(name='csa', context=statechart)
        csb = CompositeState(name='csb', context=statechart)

        # Child states
        # statechart
        statechart_init = InitialState(statechart)
        # csa
        csa_init = InitialState(csa)
        csa_hist = ShallowHistoryState(context=csa)
        A = State(name='A', context=csa)
        B = State(name='B', context=csa)
        # csb
        csb_init = InitialState(csb)
        C = State(name='C', context=csb)
        D = State(name='D', context=csb)

        # Events
        I = Event(name='I')
        J = Event(name='J')
        K = Event(name='K')
        L = Event(name='L')

        # Transitions between states & event triggers
        Transition(start=statechart_init, end=csa)
        Transition(start=csa_init, end=csa_hist)
        Transition(start=csa_hist, end=A)
        Transition(start=A, end=B, event=I)
        Transition(start=csa, end=csb, event=J)
        Transition(start=csb, end=csa, event=K)
        Transition(start=csb_init, end=C)
        Transition(start=C, end=D, event=L)

        # Execute statechart
        statechart.start()
        statechart.dispatch(I)

        # Assert we have reached state B, history should restore this state
        assert statechart.is_active('B')

        statechart.dispatch(J)

        # Assert we have reached state C
        assert statechart.is_active('C')

        statechart.dispatch(K)

        # Assert the history state has restored state B
        assert statechart.is_active('B')

    def test_activate_shallow_history_given_deep_history_scenario(self):
        """
        statechart:

        statechart_init
               |
        *** csa *******************************************          *** csc *************
        *                                                 *          *                   *
        *  csa_init--csa_hist                             *          *  csc_init         *
        *               |                                 *  --K-->  *     |             *
        *               A  --I-->  *** csb *************  *  <--L--  *     D  --M-->  E  *
        *                          *                   *  *          *                   *
        *                          *  csb_init         *  *          *********************
        *                          *     |             *  *
        *                          *     B  --J-->  C  *  *
        *                          *                   *  *
        *                          *********************  *
        *                                                 *
        ***************************************************
        """
        # Top level states
        statechart = Statechart(name='statechart')
        csa = CompositeState(name='csa', context=statechart)
        csb = CompositeState(name='csb', context=csa)
        csc = CompositeState(name='csc', context=statechart)

        # Child states
        # statechart
        statechart_init = InitialState(statechart)

        # csa
        csa_init = InitialState(csa)
        csa_hist = ShallowHistoryState(context=csa)
        A = State(name='A', context=csa)
        # csb
        csb_init = InitialState(csb)
        B = State(name='B', context=csb)
        C = State(name='C', context=csb)
        # csc
        csc_init = InitialState(csc)
        D = State(name='D', context=csc)
        E = State(name='E', context=csc)

        # Events
        I = Event(name='I')
        J = Event(name='J')
        K = Event(name='K')
        L = Event(name='L')
        M = Event(name='M')

        # Transitions between states & event triggers
        Transition(start=statechart_init, end=csa)
        Transition(start=csa_init, end=csa_hist)
        Transition(start=csa_hist, end=A)
        Transition(start=A, end=csb, event=I)
        Transition(start=csb_init, end=B)
        Transition(start=B, end=C, event=J)
        Transition(start=csa, end=csc, event=K)
        Transition(start=csc, end=csa, event=L)
        Transition(start=csc_init, end=D)
        Transition(start=D, end=E, event=M)

        # Execute statechart
        statechart.start()
        statechart.dispatch(I)

        assert statechart.is_active('B')

        statechart.dispatch(J)

        # Assert we have reached state C, history should restore C's parent
        # state csb
        assert statechart.is_active('C')

        statechart.dispatch(K)

        # Assert we have reached state D
        assert statechart.is_active('D')

        statechart.dispatch(L)

        # Assert the history state has restored state csb
        assert statechart.is_active('csb')

    def test_activate_multiple_shallow_history_states(self):
        """
        statechart:

        statechart_init
               |
        *** csa *****************************************************          *** csc *************
        *                                                           *          *                   *
        *  csa_init--csa_hist                                       *          *  csc_init         *
        *               |                                           *  --K-->  *     |             *
        *               A  --I-->  *** csb ***********************  *  <--L--  *     D  --M-->  E  *
        *                          *                             *  *          *                   *
        *                          *  csb_init--csb_hist         *  *          *********************
        *                          *               |             *  *
        *                          *               B  --J-->  C  *  *
        *                          *                             *  *
        *                          *******************************  *
        *                                                           *
        *************************************************************
        """
        # Top level states
        statechart = Statechart(name='statechart')
        csa = CompositeState(name='csa', context=statechart)
        csb = CompositeState(name='csb', context=csa)
        csc = CompositeState(name='csc', context=statechart)

        # Child states
        # statechart
        statechart_init = InitialState(statechart)

        # csa
        csa_init = InitialState(csa)
        csa_hist = ShallowHistoryState(context=csa)
        A = State(name='A', context=csa)
        # csb
        csb_init = InitialState(csb)
        csb_hist = ShallowHistoryState(context=csb)
        B = State(name='B', context=csb)
        C = State(name='C', context=csb)
        # csc
        csc_init = InitialState(csc)
        D = State(name='D', context=csc)
        E = State(name='E', context=csc)

        # Events
        I = Event(name='I')
        J = Event(name='J')
        K = Event(name='K')
        L = Event(name='L')
        M = Event(name='M')

        # Transitions between states & event triggers
        Transition(start=statechart_init, end=csa)
        Transition(start=csa_init, end=csa_hist)
        Transition(start=csa_hist, end=A)
        Transition(start=A, end=csb, event=I)
        Transition(start=csb_init, end=csb_hist)
        Transition(start=csb_hist, end=B)
        Transition(start=B, end=C, event=J)
        Transition(start=csa, end=csc, event=K)
        Transition(start=csc, end=csa, event=L)
        Transition(start=csc_init, end=D)
        Transition(start=D, end=E, event=M)

        # Execute statechart
        statechart.start()
        statechart.dispatch(I)

        assert statechart.is_active('B')

        statechart.dispatch(J)

        # Assert we have reached state C, csb's history state should restore
        # this state
        assert statechart.is_active('C')

        statechart.dispatch(K)

        # Assert we have reached state D
        assert statechart.is_active('D')

        statechart.dispatch(L)

        # Assert the history state has restored state C
        assert statechart.is_active('C')


class TestChoiceState:
    def test_create_choice_state(self):
        startchart = Statechart(name='statechart')
        composite_state = CompositeState(name='composite', context=startchart)
        ShallowHistoryState(composite_state)

    @pytest.mark.parametrize('choice, expected_state_name',
                             [('a', 'a'),
                              ('b', 'b')])
    def test_choice_state_transitions(self, choice, expected_state_name):
        class MyMetadata(Metadata):
            def __init__(self):
                super().__init__()
                self.value = None

        class IsA(Guard):
            def check(self, metadata, event):
                return metadata.value == 'a'

        myMetadata = MyMetadata()
        myMetadata.value = choice
        statechart = Statechart(name='statechart', metadata=myMetadata)
        init = InitialState(statechart)

        state_a = State(name='a', context=statechart)
        state_b = State(name='b', context=statechart)

        choice = ChoiceState(context=statechart)

        Transition(start=init, end=choice)

        Transition(start=choice, end=state_a, event=None, guard=IsA())
        Transition(start=choice, end=state_b, event=None, guard=ElseGuard())

        statechart.start()

        assert statechart.is_active(expected_state_name)
