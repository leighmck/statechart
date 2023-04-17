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

from statechart import (ChoiceState, CompositeState, Event, InitialState, ShallowHistoryState,
                        State, Statechart, Transition)


class TestInitialState:
    def test_create_initial_state(self):
        startchart = Statechart(name='statechart')
        InitialState(startchart)

    @pytest.mark.asyncio
    async def test_activate_initial_state(self):
        startchart = Statechart(name='statechart')
        initial_state = InitialState(startchart)
        default_state = State(name='default', context=startchart)
        Transition(start=initial_state, end=default_state)
        await startchart.start()

        await initial_state.activate(metadata=startchart.metadata, event=None)
        assert startchart.is_active('default')

    @pytest.mark.asyncio
    async def test_missing_transition_from_initial_state(self):
        startchart = Statechart(name='statechart')
        InitialState(startchart)

        with pytest.raises(RuntimeError):
            await startchart.start()

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
        startchart = Statechart(name='statechart')
        initial_state = InitialState(startchart)
        default_state = State(name='default', context=startchart)

        def my_guard(**kwargs):
            return False

        with pytest.raises(RuntimeError):
            Transition(start=initial_state, end=default_state, event=None, guard=my_guard)


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

    @pytest.mark.asyncio
    async def test_activate_shallow_history_state(self):
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
        csa_state = CompositeState(name='csa', context=statechart)
        csb_state = CompositeState(name='csb', context=statechart)

        # Child states
        # statechart
        statechart_init = InitialState(statechart)
        # csa
        csa_initial_state = InitialState(csa_state)
        csa_history_state = ShallowHistoryState(context=csa_state)
        csa_state_a = State(name='A', context=csa_state)
        csa_state_b = State(name='B', context=csa_state)
        # csb
        csb_init = InitialState(csb_state)
        csb_state_c = State(name='C', context=csb_state)
        csa_state_d = State(name='D', context=csb_state)

        # Events
        csa_a_to_b = Event(name='csa_a_to_b')
        csa_to_csb = Event(name='csa_to_csb')
        csb_to_csa = Event(name='csb_to_csa')
        csb_c_to_d = Event(name='csb_c_to_d')

        # Transitions between states & event triggers
        Transition(start=statechart_init, end=csa_state)
        Transition(start=csa_initial_state, end=csa_history_state)
        Transition(start=csa_history_state, end=csa_state_a)
        Transition(start=csa_state_a, end=csa_state_b, event=csa_a_to_b)
        Transition(start=csa_state, end=csb_state, event=csa_to_csb)
        Transition(start=csb_state, end=csa_state, event=csb_to_csa)
        Transition(start=csb_init, end=csb_state_c)
        Transition(start=csb_state_c, end=csa_state_d, event=csb_c_to_d)

        # Execute statechart
        await statechart.start()
        await statechart.dispatch(csa_a_to_b)

        # Assert we have reached CSA child state B, history should restore this state
        assert statechart.is_active(csa_state_b.name)

        await statechart.dispatch(csa_to_csb)

        # Assert we have reached CSB child state C
        assert statechart.is_active(csb_state_c.name)

        await statechart.dispatch(csb_to_csa)

        # Assert the history state has restored CSA child state B,
        assert statechart.is_active(csa_state_b.name)

    @pytest.mark.asyncio
    async def test_activate_shallow_history_given_deep_history_scenario(self):
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
        """  # noqa
        # Top level states
        statechart = Statechart(name='statechart')
        csa = CompositeState(name='csa', context=statechart)
        csb = CompositeState(name='csb', context=csa)
        csc = CompositeState(name='csc', context=statechart)

        # Child states
        # statechart
        statechart_init = InitialState(statechart)

        # csa
        csa_initial_state = InitialState(csa)
        csa_history_state = ShallowHistoryState(context=csa)
        csa_state_a = State(name='A', context=csa)
        # csb
        csb_init = InitialState(csb)
        csb_state_b = State(name='csb_state_b', context=csb)
        csb_state_c = State(name='csb_state_c', context=csb)
        # csc
        csc_initial_state = InitialState(csc)
        csc_state_d = State(name='csc_state_d', context=csc)
        csc_state_e = State(name='csc_state_e', context=csc)

        # Events
        csa_state_b_to_csb = Event(name='csa_state_b_to_csb')
        csb_state_b_to_csb_state_b = Event(name='csb_state_b_to_csb_state_b')
        csa_to_csc = Event(name='csa_to_csc')
        csc_to_csa = Event(name='csc_to_csa')
        csc_state_d_to_csc_state_d = Event(name='csc_state_d_to_csc_state_d')

        # Transitions between states & event triggers
        Transition(start=statechart_init, end=csa)
        Transition(start=csa_initial_state, end=csa_history_state)
        Transition(start=csa_history_state, end=csa_state_a)
        Transition(start=csa_state_a, end=csb, event=csa_state_b_to_csb)
        Transition(start=csb_init, end=csb_state_b)
        Transition(start=csb_state_b, end=csb_state_c, event=csb_state_b_to_csb_state_b)
        Transition(start=csa, end=csc, event=csa_to_csc)
        Transition(start=csc, end=csa, event=csc_to_csa)
        Transition(start=csc_initial_state, end=csc_state_d)
        Transition(start=csc_state_d, end=csc_state_e, event=csc_state_d_to_csc_state_d)

        # Execute statechart
        await statechart.start()
        await statechart.dispatch(csa_state_b_to_csb)

        assert statechart.is_active('csb_state_b')

        await statechart.dispatch(csb_state_b_to_csb_state_b)

        # Assert we have reached state csb_state_c, history should restore csb_state_c's parent
        # state csb
        assert statechart.is_active('csb_state_c')

        await statechart.dispatch(csa_to_csc)

        # Assert we have reached state csc_state_d
        assert statechart.is_active('csc_state_d')

        await statechart.dispatch(csc_to_csa)

        # Assert the history state has restored state csb
        assert statechart.is_active('csb')

    @pytest.mark.asyncio
    async def test_activate_multiple_shallow_history_states(self):
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
        csa_initial_state = InitialState(csa)
        csa_history_state = ShallowHistoryState(context=csa)
        csa_state_a = State(name='csa_state_a', context=csa)
        # csb
        csb_initial_state = InitialState(csb)
        csb_history_state = ShallowHistoryState(context=csb)
        csb_state_b = State(name='csb_state_b', context=csb)
        csb_state_c = State(name='csb_state_c', context=csb)
        # csc
        csc_initial_state = InitialState(csc)
        csc_state_d = State(name='csc_state_d', context=csc)
        csc_state_e = State(name='csc_state_e', context=csc)

        # Events
        csa_state_a_to_csb = Event(name='csa_state_a_to_csb')
        csb_state_b_to_csb_state_b = Event(name='csb_state_b_to_csb_state_b')
        csa_to_csc = Event(name='csa_to_csc')
        csc_to_sca = Event(name='csc_to_sca')
        csc_state_d_to_csc_state_e = Event(name='csc_state_d_to_csc_state_e')

        # Transitions between states & event triggers
        Transition(start=statechart_init, end=csa)
        Transition(start=csa_initial_state, end=csa_history_state)
        Transition(start=csa_history_state, end=csa_state_a)
        Transition(start=csa_state_a, end=csb, event=csa_state_a_to_csb)
        Transition(start=csb_initial_state, end=csb_history_state)
        Transition(start=csb_history_state, end=csb_state_b)
        Transition(start=csb_state_b, end=csb_state_c, event=csb_state_b_to_csb_state_b)
        Transition(start=csa, end=csc, event=csa_to_csc)
        Transition(start=csc, end=csa, event=csc_to_sca)
        Transition(start=csc_initial_state, end=csc_state_d)
        Transition(start=csc_state_d, end=csc_state_e, event=csc_state_d_to_csc_state_e)

        # Execute statechart
        await statechart.start()
        await statechart.dispatch(csa_state_a_to_csb)

        assert statechart.is_active('csb_state_b')

        await statechart.dispatch(csb_state_b_to_csb_state_b)

        # Assert we have reached state csb_state_c, csb's history state should restore
        # this state
        assert statechart.is_active('csb_state_c')

        await statechart.dispatch(csa_to_csc)

        # Assert we have reached state csc_state_d
        assert statechart.is_active('csc_state_d')

        await statechart.dispatch(csc_to_sca)

        # Assert the history state has restored state csb_state_c
        assert statechart.is_active('csb_state_c')


class TestChoiceState:
    def test_create_choice_state(self):
        startchart = Statechart(name='statechart')
        composite_state = CompositeState(name='composite', context=startchart)
        ShallowHistoryState(composite_state)

    @pytest.mark.parametrize('state_name, expected_state_name',
                             [('a', 'a'),
                              ('b', 'b')])
    @pytest.mark.asyncio
    async def test_choice_state_transitions(self, state_name, expected_state_name):
        def is_a(**kwargs):
            return state_name == 'a'

        statechart = Statechart(name='statechart')
        init = InitialState(statechart)

        state_a = State(name='a', context=statechart)
        state_b = State(name='b', context=statechart)

        choice = ChoiceState(context=statechart)

        Transition(start=init, end=choice)

        Transition(start=choice, end=state_a, event=None, guard=is_a)
        Transition(start=choice, end=state_b, event=None, guard=None)  # else

        await statechart.start()

        assert statechart.is_active(expected_state_name)
