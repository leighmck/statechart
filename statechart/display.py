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

import uuid

from statechart import (CallAction, CallGuard, ChoiceState, ConcurrentState, CompositeState,
                        ElseGuard, EqualGuard, FinalState, InitialState, ShallowHistoryState,
                        __version__)


class Display:
    """Generate code of statechart models for common graphing languages."""

    def plantuml(self, statechart):
        """
        Generate PlantUML code of a statechart model.

        Args:
            statechart (Statechart): Statechart model to generate Plant UML code.

        Returns:
            str: PlantUML description of the statechart. This string can be passed to a PlantUML
                renderer to generate statechart images.
        """

        result = [
            '@startuml',
        ]

        (states, transitions) = self.describe(state=statechart.initial_state,
                                              states=[],
                                              transitions=[])

        result += self._puml_context(context=statechart, states=states)

        result += self._puml_transitions(transitions)

        result += [
            'right footer generated by statechart v%s' % __version__,
            '@enduml'
        ]

        return '\n'.join(result)

    def describe(self, state, states, transitions):
        """
        Use a 'depth first search' to capture all states and transitions.

        Given a root state (typically the initial state of a statechart), explore a transition
        path as far as possible before backtracking to find another path.

        Args:
            statechart (Statechart): Statechart to describe.
            state (State): State node to branch out from.

        Returns:
            (tuple): tuple containing:
                states (List[State]): List of states within the statechart.
                transitions (List[Transition]): List of transitions within the statechart.
        """
        state.uuid = ''.join(('node_', str(uuid.uuid4()))).replace('-', '_')
        states.append(state)

        for transition in state._transitions:
            transitions.append(transition)

            node = transition.end
            if node not in states:
                (states, transitions) = self.describe(state=node,
                                                      states=states,
                                                      transitions=transitions)

            if isinstance(node, CompositeState):
                (states, transitions) = self.describe(state=node.initial_state,
                                                      states=states,
                                                      transitions=transitions)
            elif isinstance(node, ConcurrentState):
                for region in node._regions:
                    (states, transitions) = self.describe(state=region,
                                                          states=states,
                                                          transitions=transitions)
                    (states, transitions) = self.describe(state=region.initial_state,
                                                          states=states,
                                                          transitions=transitions)

        return (states, transitions)

    def _gen_action_name(self, action):
        """
        Generate action name.

        Extract the callback name for CallActions.

        Extend to define action names for CallAction subclasses.

        Args:
            action (Action): Action used to generate name.s

        Returns:
            str: Generated action name.
        """
        name = ''

        if isinstance(action, CallAction):
            name = action._callback.__name__
        else:
            name = 'action'

        return name

    def _gen_guard_name(self, guard):
        """
        Generate guard name.

        Extract the callback name for CallGuards.

        Extend to define action names for Guard subclasses.

        Args:
            guard (Guard): Guard used to generate name.

        Returns:
            str: Generated action name.
        """
        name = ''

        if isinstance(guard, CallGuard):
            name = guard._callback.__name__
        elif isinstance(guard, ElseGuard):
            name = 'else'
        elif isinstance(guard, EqualGuard):
            a = guard._a
            b = guard._b
            name = '{a}=={b}'.format(a=a, b=b)
        else:
            name = 'guard'

        return name

    def _gen_state_name(self, state):
        """
        Generate state name.

        Generate empty name for a choice state, it is distinguished using a diamond shape instead.
        Generate 'H' for a Shallow History state.

        Extend to define state names for State subclasses.

        Args:
            guard (Guard): Guard used to generate name.

        Returns:
            str: Generated state name.
        """
        if isinstance(state, ChoiceState):
            return ''
        elif isinstance(state, ShallowHistoryState):
            return 'H'
        else:
            return state.name

    def _puml_concurrent(self, concurrent, states):
        """
        Describe concurrent state in PlantUML syntax.

        Args:
            concurrent: Concurrent state to describe.

        Returns:
            List[str]: PlantUML description of the concurrent.
        """
        result = [
            'state {uuid} as "{name}" {{'.format(uuid=concurrent.uuid, name=concurrent.name),
        ]

        for region in concurrent._regions:
            result += self._puml_context(region, states)

            if not region == concurrent._regions[-1]:
                result += [
                    '--'
                ]

        result += [
            '}'
        ]

        return result

    def _puml_composite(self, composite, states):
        """
        Describe composite state in PlantUML syntax.

        Args:
            composite: Composite state to describe.

        Returns:
            List[str]: PlantUML description of the composite.
        """
        result = [
            'state {uuid} as "{name}" {{'.format(uuid=composite.uuid, name=composite.name),
        ]

        result += self._puml_context(composite, states)

        result += [
            '}'
        ]

        return result

    def _puml_context(self, context, states):
        """
        Describe context in PlantUML syntax.

        Args:
            context: Context to describe.

        Returns:
            List[str]: PlantUML description of the context.
        """
        result = []

        for state in states:
            if state.context is context:
                if isinstance(state, CompositeState):
                    result += self._puml_composite(composite=state, states=states)
                elif isinstance(state, ConcurrentState):
                    result += self._puml_concurrent(concurrent=state, states=states)
                else:
                    result += self._puml_state(state)

                for transition in state._transitions:
                    if isinstance(transition.end, FinalState):
                        result += self._puml_transition(transition)

        result += [
            '[*] --> {uuid}'.format(uuid=context.initial_state._transitions[0].end.uuid),
        ]

        return result

    def _puml_state(self, state):
        """
        Describe state in PlantUML syntax.

        Args:
            state: State to describe.

        Returns:
            List[str]: PlantUML description of the state.
        """
        result = []

        if isinstance(state, InitialState) or isinstance(state, FinalState):
            pass
        elif isinstance(state, ChoiceState):
            result += [
                'state {uuid} <<choice>>'.format(uuid=state.uuid)
            ]
        else:
            result += [
                'state {uuid} as "{name}"'.format(uuid=state.uuid, name=self._gen_state_name(state))
            ]

        return result

    def _puml_transition(self, transition):
        """
        Describe transition in PlantUML syntax.

        Args:
            transition: Transition to describe.

        Returns:
            List[str]: PlantUML description of the transition.
        """
        result = []

        if isinstance(transition.start, InitialState):
            start = '[*]'
            end = transition.end.uuid
        elif isinstance(transition.end, FinalState):
            start = transition.start.uuid
            end = '[*]'
        else:
            start = transition.start.uuid
            end = transition.end.uuid

        result += [
            '{start} --> {end}{div}{event}{guard}{action}'.format(
                start=start,
                end=end,
                div=' :' if transition.event or transition.action or transition.guard else '',
                event=' {}'.format(transition.event.name) if transition.event else '',
                guard=' [{}]'.format(
                    self._gen_guard_name(transition.guard)) if transition.guard else '',
                action=' / {}'.format(
                    self._gen_action_name(transition.action)) if transition.action else '')
        ]

        return result

    def _puml_transitions(self, transitions):
        """
        Describe all transitions in PlantUML syntax.

        Args:
            transitions: Transitions to describe.

        Returns:
            List[str]: PlantUML description of the transitions.
        """
        result = []

        for transition in transitions:
            if isinstance(transition.start, InitialState):
                continue

            if isinstance(transition.end, FinalState):
                continue

            result += self._puml_transition(transition)

        return result
