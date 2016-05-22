#!/usr/bin/env python2

import logging
import logging.handlers

from transitions import logger as tr_logger

from louie import plugin
from louie import dispatcher

from transitions import Machine

from twisted.internet import reactor, defer
from twisted.internet.serialport import SerialPort

from serial import PARITY_NONE
from serial import STOPBITS_ONE
from serial import EIGHTBITS

from pymdb.protocol.mdb import MDB
from pymdb.device.changer import Changer, COINT_ROUTING
from pymdb.device.bill_validator import BillValidator

from ..fsm.changer_fsm import ChangerWrapper, ChangerFSM

plugin.install_plugin(plugin.TwistedDispatchPlugin())


logger = logging.getLogger('pymdb')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    'pymdb.log', maxBytes=1028576, backupCount=10)
form = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)s:%(message)s')
handler.setFormatter(form)
logger.addHandler(handler)

logger = logging.getLogger('kiosk')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    'kiosk.log', maxBytes=1028576, backupCount=10)
form = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)s:%(message)s')
handler.setFormatter(form)
logger.addHandler(handler)

tr_logger.addHandler(handler)
tr_logger.setLevel(logging.DEBUG)


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
        states = ["ready", "summing", "prepare", "dispense",
                  "accept_bill", 'return_bill', 'accept_bill']
        transitions = [
            # trigger,         source,          dest,      conditions,       unless,          before,          after
            ['sell',           'ready',        'summing',      None,          None,         'set_product',     None        ],
            ['coin_in',        'summing',      'prepare',     'is_enough',    None,         'add_amount',     'stop_accept'],
            ['coin_in',        'summing',      'summing',      None,         'is_enough',   'add_amount',      None        ],
            ['bill_in',        'summing',      'accept_bill', 'check_bill',   None,           None,            None        ],
            ['bill_in',        'summing',      'return_bill',  None,         'check_bill',    None,            None        ],
            ['bill_returned',  'return_bill',  'summing',      None,         'check_bill',    None,            None        ],
            ['bill_stacked',   'accept_bill',  'prepare',     'is_enough',    None,          'add_amount',     None        ],
            ['bill_stacked',   'accept_bill',  'summing',      None,         'is_enough',    'add_amount',    'stop_accept'],
            ['prepared',       'prepare',      'dispense',     None,         'is_dispensed',  None,            None        ],
            ['prepared',       'prepare',      'ready',       'is_dispensed', None,           None,           'clear_summ' ],
            ['coin_out',       'dispense',     'dispense',     None,         'is_dispensed', 'remove_amount',  None        ],
            ['coin_out',       'dispense',     'ready',       'is_dispensed', None,          'remove_amount', 'clear_summ' ],
        ]
        super(Kiosk2, self).__init__(
            states=states, transitions=transitions, initial='ready')
        self.changer = changer
        dispatcher.connect(self.coin_in, sender=changer, signal='coin_in')
        self.summ = 0

    @defer.inlineCallbacks
    def start(self):
        yield self.changer.reset()
        self.changer.start_polling()

    def add_amount(self, amount):
        logger.debug('add amount {}'.format(amount))
        self.summ += amount

    def start_accept(self):
        logger.debug('start accept')
        self.changer.start_accept()

    def stop_accept(self, amount):
        logger.debug('stop accept')
        self.changer.stop_accept()

    def set_product(self, product):
        self.product = product
        self.start_accept()

    def check_bill(self, bill):
        return bill == 10

    def is_enough(self, amount):
        logger.debug("check for enough, need {}, have {}".format(
            self.product, self.summ+amount))
        return self.summ + amount >= self.product

    def remove_amount(self, amount):
        self.summ -= amount

    def is_dispensed(self, amount=0):
        return (self.summ - amount - self.product) <= 0

    def clear_summ(self, amount=0):
        self.summ = 0


# class RUChanger(Changer):
# 
#     COINS = {
#         0: 1,
#         1: 2,
#         2: 5,
#         4: 10
#     }
# 
#     def __init__(self, proto):
#         super(RUChanger, self).__init__(proto)
# 
#     def start_accept(self):
#         return self.coin_type(coins='\xFF\xFF')
# 
#     def stop_accept(self):
#         return self.coin_type(coins='\x00\x00')
# 
#     def deposited(self, coin, routing=1, in_tube=None):
#         logger.debug(
#             "Coin deposited({}): {}".format(
#                 COINT_ROUTING[routing], self.COINS[coin]))
#         if routing == 1:
#             amount = self.COINS[coin]
#             dispatcher.send_minimal(
#                 sender=self, signal='coin_in', amount=amount)
# 
#     def dispense_all(self):
# 	#logger.debug("coin_count:  0x%0.2X" % self.coin_count[2])
#         self.dispense(coin=0, count=10)
#         self.dispense(coin=1, count=10)
#         self.dispense(coin=2, count=10)
#         self.dispense(coin=4, count=10)

class RUChangerFSM(ChangerFSM):

    def __init__(self, changer, amount=30):
        super(RUChangerFSM, self).__init__(changer)
        self.amount = amount
        
    def check_coin(self, amount):
        accepted_amount = self._accepted_amount
        need_amount = self.amount
        if accepted_amount >= need_amount:
            self.invalid_coin(amount)
        elif accepted_amount + amount >= need_amount:
            self.valid_coin(amount)
            self.stop_accept()
            self.dispense_amount(accepted_amount+amount-need_amount)
        elif not self.can_dispense_amount(accepted_amount + amount):
            self.invalid_coin(amount)
        else:
            self.valid_coin(amount)


class RUChanger(ChangerWrapper):

    COINS = {
        0: 1,
        1: 2,
        2: 5,
        4: 10
    }

    def __init__(self, proto):
        super(RUChanger, self).__init__(proto, COINS)

    def dispense_all(self):
    #logger.debug("coin_count:  0x%0.2X" % self.coin_count[2])
        self.dispense(coin=0, count=10)
        self.dispense(coin=1, count=10)
        self.dispense(coin=2, count=10)
        self.dispense(coin=4, count=10)


class RUBillValidator(BillValidator):

    def __init__(self, proto):
        super(RUBillValidator, self).__init__(proto)

    def start_accept(self):
        return self.bill_type(bills='\xFF\xFF\xFF\xFF')

    def stop_accept(self):
        return self.bill_type(bills='\x00\x00\x00\x00')



if __name__ == '__main__':
    proto = MDB()
    SerialPort(
        #  proto, '/dev/ttyUSB0', reactor,
        proto, '/dev/ttyMDB', reactor,
        baudrate='38400', parity=PARITY_NONE,
        bytesize=EIGHTBITS, stopbits=STOPBITS_ONE)
    changer = RUChanger(proto)
    changerFsm = RUChangerFSM(changer=changer)
        
    #validator = RUBillValidator(proto)
    #kiosk = Kiosk2(changer)
    
    #reactor.callLater(0, proto.mdb_init)
    
    reactor.callLater(0, changerFsm.start)
    reactor.callLater(5, changerFsm.start_accept)
    #reactor.callLater(3, changerFsm.dispense_amount, 100)
    #reactor.callLater(10, changerFsm.stop)

    #reactor.callLater(1, changer.reset)
    #reactor.callLater(2, changer.start_polling)
    #reactor.callLater(3, changer.dispense, coin=0, count=5)
    #reactor.callLater(4, changer.dispense, coin=1, count=5)
    #reactor.callLater(5, changer.dispense, coin=2, count=5)
    #reactor.callLater(6, changer.dispense, coin=4, count=5)
    #reactor.callLater(3, changer.define_coin_count)
    #reactor.callLater(4, changer.dispense_all)
    #reactor.callLater(10, changer.start_accept)

    #reactor.callLater(1, validator.reset)
    #reactor.callLater(2, validator.start_polling)
    #reactor.callLater(3, validator.escrow)
    #reactor.callLater(4, validator.start_accept)
    #reactor.callLater(12, validator.stop_accept)
    #reactor.callLater(13, validator.escrow)

    #reactor.callLater(10, validator.stop_accept)



    #  reactor.callLater(1, kiosk.start)
    #  kiosk = Kiosk(proto)
    #  reactor.callLater(0, kiosk.loop)
    #  reactor.callLater(3, kiosk.sell, 15)
    #  reactor.callLater(15, kiosk.stop_changer)
    #  ckkklogger.debug("run reactor")


    reactor.run()
