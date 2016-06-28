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

import asyncio
import logging

import websockets

from statechart import CompositeState, Event, InitialState, State, Statechart, Transition

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
statechart = Statechart(name='statecart', param=0)
csa = CompositeState(name='csa', context=statechart)
csb = CompositeState(name='csb', context=csa)
csc = CompositeState(name='csc', context=statechart)

# Child states
# statechart
statechart_init = InitialState(name='statechart_init', context=statechart)

# csa
csa_init = InitialState(name='csa_init', context=csa)
A = State(name='A', context=csa)
# csb
csb_init = InitialState(name='csb_init', context=csb)
B = State(name='B', context=csb)
C = State(name='C', context=csb)
# csc
csc_init = InitialState(name='csc_init', context=csc)
D = State(name='D', context=csc)
E = State(name='E', context=csc)

# Events
I = Event(name='I', param=0)
J = Event(name='J', param=0)
K = Event(name='K', param=0)
L = Event(name='L', param=0)
M = Event(name='M', param=0)

# Transitions between states & event triggers
Transition(name='statechart_init_default', start=statechart_init, end=csa)
Transition(name='csa_init_default', start=csa_init, end=A)
Transition(name='AtoCsb', start=A, end=csb, event=I)
Transition(name='csb_init_default', start=csb_init, end=B)
Transition(name='BtoC', start=B, end=C, event=J)
Transition(name='CsaToCsc', start=csa, end=csc, event=K)
Transition(name='CscToCsa', start=csc, end=csa, event=L)
Transition(name='csc_init_default', start=csc_init, end=D)
Transition(name='DtoE', start=D, end=E, event=M)

statechart.start()


async def web_app():
    await statechart.sc_loop()


async def hello(websocket, path):
    while True:
        event = await websocket.recv()
        statechart.async_handle_event(Event(name=event, param=0))
        print("< {}".format(event))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    handler = logging.FileHandler('statechart.log')
    handler.setLevel(logging.INFO)

    loop = asyncio.get_event_loop()
    app_server = websockets.serve(hello, 'localhost', 8888)

    tasks = [app_server, asyncio.ensure_future(web_app())]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.run_forever()

    loop.close()
