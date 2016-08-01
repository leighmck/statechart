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

from statechart import Action, CallAction, Metadata


class MyAction(Action):
    def execute(self, metadata, event):
        pass


class MyMetadata(Metadata):
    def __init__(self):
        super().__init__()
        self.value = 0


@pytest.fixture
def my_action():
    return MyAction()


@pytest.fixture
def my_metadata():
    return MyMetadata()


class TestAction:
    def test_abstract_instantiation_throws(self):
        with pytest.raises(TypeError):
            Action()

    def test_execute_action(self, my_action):
        my_action.execute(metadata=None, event=None)


def my_callback(metadata, event):
    metadata.value = 1


class TestCallAction:
    def test_execute_callback_action(self, my_metadata):
        call_action = CallAction(my_callback)
        call_action.execute(metadata=my_metadata, event=None)
        assert my_metadata.value is 1
