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


class StateRuntimeData:
    """
    Holds the runtime specific data for a state in the statechart.
    """

    def __init__(self):
        self.current_state = None
        self.state_set = list()


class Metadata:
    """
    Describes runtime specific data of the statechart. The main data is the
    currently active state. For every active state a StateRuntimeData object is
    created which stores specific data for the state. This object is allocated
    only when the state is active, otherwise it is deleted.
    """

    def __init__(self):
        self.active_states = {}
        self.event = None
        self.history_states = {}
        self.transition = None

    def activate(self, state):
        """
        Activates a state for this Metadata. If the state is not already
        active, it will be added and a new StateRuntimeData created.

        :param state: State to activate.
        """
        if not (state in self.active_states):
            self.active_states[state] = StateRuntimeData()

        data = self.active_states[state]
        data.current_state = None

        if state.context:
            if state.context not in self.active_states:
                raise RuntimeError('Parent state not activated')

            data = self.active_states[state.context]
            data.current_state = state

    def deactivate(self, state):
        """
        Deactivates the state and frees the allocated resources.

        :param state: State to deactivate.
        """
        if state in self.active_states:
            data = self.active_states[state]
            data.current_state = None
            data = None
            del self.active_states[state]

    def is_active(self, state):
        """
        Checks whether the given state is active or not.

        :param state: State to check.
        :return: True is the state is active.
        """
        status = False

        if state in self.active_states:
            status = True

        return status

    def reset(self):
        """Resets the metadata object for reuse."""
        self.active_states.clear()
