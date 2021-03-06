#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
##
## Grundfos GENIBus Library for Arduino.
##
## (C) 2007-2014 by Christoph Schueler <github.com/Christoph2,
##                                      cpu12.gems@googlemail.com>
##
##  All Rights Reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program; if not, write to the Free Software Foundation, Inc.,
## 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##
##

import abc
import logging
import threading
#from wx.lib.pubsub import Publisher as Publisher
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub as Publisher
from genilib.configuration import Config
from wx import CallAfter

logger = logging.getLogger("GeniControl")

DATA_NOT_AVAILABLE = None
config = Config("GeniControl")

class IController(object):
    __metaclass__ = abc.ABCMeta
    logger = logging.getLogger("GeniControl")
    quitViewEvent = threading.Event()
    quitModelEvent = threading.Event()

    def __init__(self, modelCls, viewClass):
        self._pub = Publisher
        self._view = viewClass  # (self, model)
        self._waitingPoint = threading.Event()
        connection = connectionFactory(config.get('network', 'driver'))
        self._model = modelCls(self._waitingPoint, connection)
        setattr(self._model, '_controller', self)
        self._viewThread = self._view.initialize(self._model, IController.quitViewEvent)
        self._sync = threading.RLock()
        # TODO: Create and disable controls.
        self._modelThread = self._model.initialize(IController.quitModelEvent)

    def signal(self):
        self._waitingPoint.set()

    def trace(self, rxTx, telegram):
        self._sync.acquire()
        #self._view.updateBusmonitor(rxTx, telegram)
        CallAfter(self._view.updateBusmonitor, rxTx, telegram)
        self._sync.release()


def connectionFactory(driver):
    from genicontrol.simu.Simulator import SimulationServer
    from genicontrol.tcpclient import Connector
    from genicontrol.serialport import SerialPort, serialAvailable

    ip = config.get('network', 'serverip')
    port = config.get('network', 'serverport')
    if driver == 1:
        return Connector(ip, port)
    elif driver == 2 and serialAvailable:
        serialPort = config.get('serial', 'serialport')
        if not serialPort:
            logger.error("Serial port not specified.")
            return SimulationServer()   ## Fallback to simulator.
        else:
            return SerialPort(portName = serialPort, baudrate = 9600, timeout = 0.5)
    else:
        return SimulationServer()
