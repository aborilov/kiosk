import logging

from louie import dispatcher
from pymdb.device.changer import Changer, COINT_ROUTING
from transitions import Machine
from twisted.internet import reactor, defer


logger = logging.getLogger('pymdb')

class ChangerFSM(Machine):

    def __init__(self, changer):
        
        states = ["offline", "online", "error", "ready",
                  "wait_coin", "dispense_amount"]
        transitions = [
            # trigger,                 source,            dest,              conditions,     unless,          before,           after
            ['online',                 'offline',         'online',           None,           None,            None,            '_after_online'     ],
            ['initialized',            'online',          'ready',            None,           None,            None,            '_after_init'       ],
            ['start_accept',           'ready',           'wait_coin',        None,           None,            None,            '_start_accept'     ],
            ['dispense_amount',        'ready',           'dispense_amount',  None,           None,            None,            '_start_dispense'   ],
            ['coin_in',                'wait_coin',       'ready',            None,           None,           '_stop_accept',   '_coin_in'          ],
            ['stop_accept',            'wait_coin',       'ready',            None,           None,           '_stop_accept',    None               ],
            ['coin_out',               'dispense_amount', 'dispense_amount',  None,          '_is_dispensed', '_remove_amount',  None               ],
            ['coin_out',               'dispense_amount', 'ready',           '_is_dispensed', None,           '_remove_amount', '_amount_dispensed' ],
            ['stop_dispense',          'dispense_amount', 'ready',            None,           None,            None,            '_amount_dispensed' ],
            
            ['coin_in',                'ready',           'ready',            None,           None,           '_stop_accept',   '_coin_in'          ],
            
            ['error',                  'online',          'error',            None,           None,            None,            '_after_error'      ],
            ['error',                  'ready',           'error',            None,           None,            None,            '_after_error'      ],
            ['error',                  'wait_coin',       'error',            None,           None,            None,            '_after_error'      ],
            ['error',                  'dispense_amount', 'error',            None,           None,            None,            '_after_error'      ],
            ['offline',                'online',          'offline',          None,           None,            None,            '_after_offline'    ],
            ['offline',                'ready',           'offline',          None,           None,            None,            '_after_offline'    ],
            ['offline',                'error',           'offline',          None,           None,            None,            '_after_offline'    ],
            ['offline',                'wait_coin',       'offline',          None,           None,            None,            '_after_offline'    ],
            ['offline',                'dispense_amount', 'offline',          None,           None,            None,            '_after_offline'    ],
            
        ]
        super(ChangerFSM, self).__init__(
            states=states, transitions=transitions, initial='offline')
        self.changer = changer
        dispatcher.connect(self.online, sender=changer, signal='online')
        dispatcher.connect(self.initialized, sender=changer, signal='initialized')
        dispatcher.connect(self.error, sender=changer, signal='error')
        dispatcher.connect(self.offline, sender=changer, signal='offline')
        dispatcher.connect(self.coin_in, sender=changer, signal='coin_in')
        dispatcher.connect(self.coin_out, sender=changer, signal='coin_out')
        
        # init parameters
        self._dispensed_amount = 0
    
    def start(self):
        self.changer.start_device()

    def stop(self):
        # TODO сбросить автомат
        self.changer.stop_device()
    
    def _after_online(self):
        dispatcher.send_minimal(
            sender=self, signal='online')

    def _after_offline(self):
        dispatcher.send_minimal(
            sender=self, signal='offline')

    def _after_init(self):
        dispatcher.send_minimal(
            sender=self, signal='initialized')

    def _after_error(self, error_code, error_text):
        self._stop_accept()
        dispatcher.send_minimal(
            sender=self, signal='error', error_code=error_code, error_text=error_text)

    def _amount_dispensed(self):
        dispatcher.send_minimal(
            sender=self, signal='amount_dispensed', amount=self._dispensed_amount)

    def _coin_in(self, amount):
        dispatcher.send_minimal(
            sender=self, signal='coin_in', amount=amount)

    def _start_accept(self):
        self.changer.start_accept()

    def _stop_accept(self):
        self.changer.stop_accept()

    def _start_dispense(self, amount):
        self._dispensed_amount = amount
        reactor.callLater(1, self._dispense_amount_impl, amount=amount)
 
    def _dispense_amount_impl(self, amount):
        if amount <= 0:
            self.stop_dispense()
        self.changer.dispense_amount(amount)

    def _remove_amount(self, amount):
        logger.debug("_remove_amount: {}".format(amount))
        self._dispensed_amount -= amount

    def _is_dispensed(self, amount):
        logger.debug("_is_dispensed: {}".format(amount))
        return self._dispensed_amount - amount <= 0

    def can_dispense_amount(self, amount):
        return changer.can_dispense_amount(amount)