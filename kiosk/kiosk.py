#!/usr/bin/env python2

import logging
import logging.handlers

from transitions import Machine

from twisted.internet import reactor, defer
from twisted.internet.serialport import SerialPort

from serial import PARITY_NONE
from serial import STOPBITS_ONE
from serial import EIGHTBITS

from pymdb.protocol.mdb import MDB
from pymdb.device.changer import Changer, COINT_ROUTING

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    'kiosk.log', maxBytes=1028576, backupCount=10)
form = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)s:%(message)s')
handler.setFormatter(form)
logger.addHandler(handler)


class Kiosk(object):

    def __init__(self, proto):
        self.proto = proto
        self.changer = RUChanger(proto, self)
        self.waiter = None
        #  self.bill = BillValidator(proto)

    @defer.inlineCallbacks
    def loop(self):
        yield self.proto.mdb_init()
        yield self.changer.reset()
        self.changer.start_polling()

    @defer.inlineCallbacks
    def accept(self, amount):
        yield self.changer.start_accept()
        try:
            summ = 0
            while summ < amount:
                self.waiter = defer.Deferred()
                timedefer = reactor.callLater(10, defer.timeout, self.waiter)
                s = yield self.waiter
                if timedefer.active():
                    timedefer.cancel()
                summ += s
                logger.debug("Have summ: {}".format(summ))
            logger.debug("Final summ: {}".format(summ))
            defer.returnValue(summ)
        except Exception:
            logger.exception("While get amount")
        finally:
            yield self.changer.stop_accept()

    def deposited(self, amount):
        logger.debug("Deposited: {}".format(amount))
        if self.waiter:
            self.waiter.callback(amount)


class Kiosk2(Machine):

    def __init__(self, changer):
        states = ["ready", "summing", "prepare", "dispense"]
        transitions = [
            {'trigger': 'sell', 'source': 'ready',
             'dest': 'summing', 'before': 'set_product'},
            {'trigger': 'coin_in', 'source': 'summing',
            'dest': 'prepare', 'conditions': 'is_enough'},
            {'trigger': 'prepared', 'source': 'prepare', 'dest': 'dispense'},
            {'trigger': 'coin_out', 'source': 'dispense',
             'dest': 'ready', 'conditions': 'is_dispensed',
             'after': 'clear_summ'},
        ]
        self.changer = changer
        super(Kiosk2, self).__init__(
            states=states, transitions=transitions, initial='ready')
        self.summ = 0

    def set_product(self, product):
        self.product = product

    def is_enough(self, amount):
        self.summ += amount
        return self.summ >= self.product

    def is_dispensed(self, amount):
        self.summ -= amount
        return (self.summ - self.product)<=0

    def clear_summ(self, amount):
        self.summ = 0

class RUChanger(Changer):

    COINS = {
        0: 1,
        1: 2,
        2: 5,
        4: 10
    }

    def __init__(self, proto, kiosk):
        super(RUChanger, self).__init__(proto)
        self.kiosk = kiosk

    def start_accept(self):
        return self.coin_type(coins='\xFF\xFF')

    def stop_accept(self):
        return self.coin_type(coins='\x00\x00')

    def deposited(self, coin, routing=1, in_tube=None):
        logger.debug(
            "Coin deposited({}): {}".format(
                COINT_ROUTING[routing], self.COINS[coin]))
        if routing == 1:
            self.kiosk.deposited(self.COINS[coin])


if __name__ == '__main__':
    kiosk = Kiosk2(None)
    import ipdb; ipdb.set_trace()  # XXX BREAKPOINT
    #  proto = MDB()
    #  SerialPort(
        #  #  proto, '/dev/ttyUSB0', reactor,
        #  proto, '/dev/ttyS0', reactor,
        #  baudrate='38400', parity=PARITY_NONE,
        #  bytesize=EIGHTBITS, stopbits=STOPBITS_ONE)
    #  kiosk = Kiosk(proto)
    #  reactor.callLater(0, kiosk.loop)
    #  reactor.callLater(3, kiosk.accept, 15)
    #  reactor.callLater(15, kiosk.stop_changer)
    #  ckkklogger.debug("run reactor")
    #  reactor.run()
