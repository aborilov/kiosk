import logging

from twisted.internet import reactor, defer

from louie import dispatcher

from transitions import Machine

logger = logging.getLogger('pymdb')

DEVICE_STATE_OFFLINE = 0
DEVICE_STATE_ERROR = 1
DEVICE_STATE_READY = 2

class CashFSM(Machine):

    def __init__(self, changer_fsm, validator_fsm):
        
        states = ["init", "wait_ready", "error", "ready",
                  "accept_amount", "wait_dispense", "start_dispense"]
        transitions = [
            # trigger,                   source,            dest,              conditions,      unless,             before,             after
            ['start',                    'init',            'wait_ready',       None,            None,               None,              '_after_started'        ],
            ['changer_ready',            'wait_ready',      'ready',           '_is_ready',      None,               None,              None                    ],
            ['validator_ready',          'wait_ready',      'ready',           '_is_ready',      None,               None,              None                    ],
            ['coin_in',                  'ready',           'ready',            None,            None,              '_dispense_amount', None                    ],
            ['bill_in',                  'ready',           'ready',            None,            None,              '_ban_bill',        None                    ],
            ['accept',                   'ready',           'accept_amount',    None,            None,               None,              '_start_accept'         ],
            ['accept_timeout',           'accept_amount',   'ready',            None,            None,               None,              '_after_accept_timeout' ],
            ['coin_in',                  'accept_amount',   'accept_amount',    None,            '_is_enough',       None,              '_add_amount'           ],
            ['check_bill',               'accept_amount',   'accept_amount',    None,            '_is_valid_bill',  '_ban_bill',        None                    ],
            ['check_bill',               'accept_amount',   'accept_amount',   '_is_valid_bill', '_is_enough',      '_permit_bill',     '_add_amount'           ],
            ['coin_in',                  'accept_amount',   'wait_dispense',   '_is_enough',     None,               None,              '_after_accept'         ],
            ['check_bill',               'accept_amount',   'wait_dispense',   '_is_enough',     'is_invalid_bill', '_permit_bill',     '_after_accept'         ],
            ['coin_in',                  'wait_dispense',   'wait_dispense',    None,            None,              '_add_amount',      '_amount_accepted'      ],
            ['check_bill',               'wait_dispense',   'wait_dispense',    None,            None,              '_ban_bill',        None                    ],
            ['dispense_all',             'wait_dispense',   'start_dispense',   None,            None,               None,              '_dispense_all'         ],
            ['dispense_change',          'wait_dispense',   'start_dispense',   None,            None,               None,              '_dispense_change'      ],
            ['amount_dispensed',         'start_dispense',  'ready',            None,            None,               None,              None                    ],
             
            ['changer_error',            'ready',           'error',            None,            None,               None,              '_after_error'          ],
            ['changer_error',            'accept_amount',   'error',            None,            None,               None,              '_after_error'          ],
            ['changer_error',            'wait_dispense',   'error',            None,            None,               None,              '_after_error'          ],
            ['changer_error',            'start_dispense',  'error',            None,            None,               None,              '_after_error'          ],
            ['validator_error',          'ready',           'error',            None,            None,               None,              '_after_error'          ],
            ['validator_error',          'accept_amount',   'error',            None,            None,               None,              '_after_error'          ],
            ['validator_error',          'wait_dispense',   'error',            None,            None,               None,              '_after_error'          ],
            ['validator_error',          'start_dispense',  'error',            None,            None,               None,              '_after_error'          ],
            
        ]
        super(CashFSM, self).__init__(
            states=states, transitions=transitions, initial='init')
        
        self.changer_fsm = changer_fsm
        self.validator_fsm = validator_fsm
        
        self.changer_state = DEVICE_STATE_OFFLINE
        self.validator_state = DEVICE_STATE_OFFLINE        
        
        dispatcher.connect(self._on_changer_offline, sender=changer_fsm, signal='offline')
        dispatcher.connect(self._on_changer_ready, sender=changer_fsm, signal='initialized')
        dispatcher.connect(self._on_changer_error, sender=changer_fsm, signal='error')
        dispatcher.connect(self.coin_in, sender=changer_fsm, signal='coin_in')
        dispatcher.connect(self.amount_dispensed, sender=changer_fsm, signal='amount_dispensed')
        dispatcher.connect(self._on_validator_offline, sender=validator_fsm, signal='offline')
        dispatcher.connect(self._on_validator_ready, sender=validator_fsm, signal='initialized')
        dispatcher.connect(self._on_validator_error, sender=validator_fsm, signal='error')
        dispatcher.connect(self.bill_in, sender=validator_fsm, signal='bill_in')
        dispatcher.connect(self.check_bill, sender=validator_fsm, signal='check_bill')
        
        # init parameters
        self._need_accept_amount = 0
        self._accepted_amount = 0

    def _after_started(self):
        self.changer_fsm.start()
        self.validator_fsm.start()

    def stop(self):
        # TODO reset FSM
        self.changer_fsm.stop()
        self.validator_fsm.stop()
    
    def _on_changer_ready(self):
        self.changer_state = DEVICE_STATE_READY
        self.changer_ready()
    
    def _on_changer_offline(self):
        self.changer_state = DEVICE_STATE_OFFLINE

    def _on_changer_error(self, error_code, error_text):
        self.changer_state = DEVICE_STATE_ERROR
        self.changer_error(error_code, error_text)

    def _on_validator_ready(self):
        self.validator_state = DEVICE_STATE_READY
        self.validator_ready()

    def _on_validator_offline(self):
        self.validator_state = DEVICE_STATE_OFFLINE

    def _on_validator_error(self, error_code, error_text):
        self.validator_state = DEVICE_STATE_ERROR
        self.validator_error(error_code, error_text)
    
    def _is_ready(self):
        return ((self.changer_state == DEVICE_STATE_READY) and
                (self.validator_state == DEVICE_STATE_READY))
    
    def _dispense_amount(self, amount):
        self.changer_fsm.dispense_amount(amount)
    
    def _ban_bill(self, amount):
        self.validator_fsm.ban_bill(amount)

    def _permit_bill(self, amount):
        self.validator_fsm.permit_bill(amount)
    
    def _start_accept(self, amount):
        self._need_accept_amount = amount
        self.changer_fsm.start_accept()
        self.validator_fsm.start_accept()

    def _stop_accept(self):
        self.changer_fsm.stop_accept()
        self.validator_fsm.stop_accept()
    
    def _after_accept_timeout(self):
        self._stop_accept()
        self.changer_fsm.dispense_amount(self._accepted_amount)
        dispatcher.send_minimal(
            sender=self, signal='not_accepted')

    def _add_amount(self, amount):
        self._accepted_amount += amount
        
    def _amount_accepted(self, amount=0):
        accepted_amount = self._accepted_amount + amount
        dispatcher.send_minimal(
            sender=self, signal='accepted', amount=accepted_amount)
        
    def _is_enough(self, amount):
        return self._need_accept_amount <= self._accepted_amount + amount

    def _is_valid_bill(self, amount):
        accepted_amount = self._accepted_amount + amount
        if not self.changer_fsm.can_dispense_amount(accepted_amount):
            return False
        change_amount = self._accepted_amount + amount - self._need_accept_amount
        if change_amount > 0 and not self.changer_fsm.can_dispense_amount(change_amount):
            return False
        return True
    
    def _after_accept(self, amount):
        self._add_amount(amount)
        self._stop_accept()
        self._amount_accepted()
        
    def _dispense_all(self):
        self._dispense_amount(self._accepted_amount)
            
    def _dispense_change(self):
        change_amount = self._accepted_amount - self._need_accept_amount
        self._dispense_amount(change_amount)

    def _after_error(self, error_code, error_text):
        self._stop_accept()
        dispatcher.send_minimal(
            sender=self, signal='error', error_code=error_code, error_text=error_text)
