import logging

from louie import dispatcher
from transitions import Machine

from twisted.internet import reactor
from twisted.internet.error import AlreadyCalled

logger = logging.getLogger('kiosk')

DEVICE_STATE_OFFLINE = 0
DEVICE_STATE_ERROR = 1
DEVICE_STATE_READY = 2

class CashFSM(Machine):

    def __init__(self, changer_fsm, validator_fsm):

        states = ["init", "wait_ready", "error", "ready",
                  "accept_amount", "wait_dispense", "start_dispense"]
        transitions = [
            # trigger,                   source,            dest,              conditions,      unless,             before,               after
            ['start',                    'init',            'wait_ready',       None,            '_is_ready',        None,                '_after_started'        ],
            ['start',                    'init',            'ready',           '_is_ready',      None,              '_after_started',     '_after_ready'          ],
            ['changer_ready',            'wait_ready',      'ready',           '_is_ready',      None,               None,                '_after_ready'          ],
            ['validator_ready',          'wait_ready',      'ready',           '_is_ready',      None,               None,                '_after_ready'          ],
            ['coin_in',                  'ready',           'ready',            None,            None,              '_dispense_amount',   None                    ],
#             ['bill_in',                  'ready',           'ready',            None,            None,              '_ban_bill',          None                    ],
            ['accept',                   'ready',           'accept_amount',    None,            None,               None,                '_start_accept'         ],
            ['accept_timeout',           'accept_amount',   'ready',            None,            None,               None,                '_after_accept_timeout' ],
            ['changer_ready',            'accept_amount',   'accept_amount',    None,            None,               None,                '_start_coin_accept'    ],
            ['validator_ready',          'accept_amount',   'accept_amount',    None,            None,               None,                '_start_bill_accept'    ],
            ['coin_in',                  'accept_amount',   'accept_amount',    None,            '_is_enough',      '_start_coin_accept', '_add_amount'           ],
            ['coin_in',                  'accept_amount',   'accept_amount',   '_is_enough',    '_is_valid_coin',   ['_reset_acceptance_monitor',
                                                                                                                     '_start_coin_accept'], '_dispense_amount'      ],
            ['bill_in',                  'accept_amount',   'accept_amount',    None,            '_is_enough',      '_start_bill_accept', '_add_amount'           ],
            ['check_bill',               'accept_amount',   'accept_amount',    None,            '_is_valid_bill',  '_ban_bill',          '_start_bill_accept'    ],
            ['check_bill',               'accept_amount',   'accept_amount',   '_is_valid_bill', None,              '_permit_bill',       None                    ],
            ['coin_in',                  'accept_amount',   'wait_dispense',   ['_is_enough',
                                                                              '_is_valid_coin'], None,               None,                '_after_accept'         ],
            ['bill_in',                  'accept_amount',   'wait_dispense',   '_is_enough',     None,               None,                '_after_accept'         ],
            ['coin_in',                  'wait_dispense',   'wait_dispense',    None,            None,              '_add_amount',        '_amount_accepted'      ],
            ['bill_in',                  'wait_dispense',   'wait_dispense',    None,            None,              '_add_amount',        '_amount_accepted'      ],
            ['dispense_all',             'wait_dispense',   'start_dispense',   None,            None,               None,                '_dispense_all'         ],
            ['dispense_change',          'wait_dispense',   'start_dispense',   None,            None,               None,                '_dispense_change'      ],
            ['amount_dispensed',         'start_dispense',  'ready',            None,            None,               None,                '_amount_dispensed'     ],
            ['changer_offline',          'start_dispense',  'ready',            None,            None,               None,                '_amount_dispensed'     ],

            ['check_bill',               'init',            'init',             None,            None,              '_ban_bill',          None                    ],
            ['check_bill',               'wait_ready',      'wait_ready',       None,            None,              '_ban_bill',          None                    ],
            ['check_bill',               'ready',           'ready',            None,            None,              '_ban_bill',          None                    ],
            ['check_bill',               'wait_dispense',   'wait_dispense',    None,            None,              '_ban_bill',          None                    ],
            ['check_bill',               'start_dispense',  'start_dispense',   None,            None,              '_ban_bill',          None                    ],
            ['check_bill',               'error',           'error',            None,            None,              '_ban_bill',          None                    ],

            ['dispense_all',             'error',           'error',            None,            None,               None,                '_dispense_all'         ],
            ['dispense_change',          'error',           'error',            None,            None,               None,                '_dispense_change'      ],

            ['changer_error',            'ready',           'error',            None,            None,               None,                '_after_error'          ],
            ['changer_error',            'accept_amount',   'error',            None,            None,               None,                '_after_error'          ],
            ['changer_error',            'wait_dispense',   'error',            None,            None,               None,                '_after_error'          ],
            ['changer_error',            'start_dispense',  'error',            None,            None,               None,                '_after_error'          ],
            ['validator_error',          'ready',           'error',            None,            None,               None,                '_after_error'          ],
            ['validator_error',          'accept_amount',   'error',            None,            None,               None,                '_after_error'          ],
            ['validator_error',          'wait_dispense',   'error',            None,            None,               None,                '_after_error'          ],
            ['validator_error',          'start_dispense',  'error',            None,            None,               None,                '_after_error'          ],

        ]
        super(CashFSM, self).__init__(
            states=states,
            transitions=transitions,
            initial='init',
            ignore_invalid_triggers=True)

        self.changer_fsm = changer_fsm
        self.validator_fsm = validator_fsm

        self.changer_state = DEVICE_STATE_OFFLINE
        self.validator_state = DEVICE_STATE_OFFLINE

        dispatcher.connect(self._on_changer_offline,
                           sender=changer_fsm, signal='offline')
        dispatcher.connect(self._on_changer_ready, 
                           sender=changer_fsm, signal='initialized')
        dispatcher.connect(self._on_changer_error, 
                           sender=changer_fsm, signal='error')
        dispatcher.connect(self._on_coin_in, sender=changer_fsm, signal='coin_in')
        dispatcher.connect(self.amount_dispensed, 
                           sender=changer_fsm, signal='amount_dispensed')
        dispatcher.connect(self._on_validator_offline, 
                           sender=validator_fsm, signal='offline')
        dispatcher.connect(self._on_validator_ready, 
                           sender=validator_fsm, signal='initialized')
        dispatcher.connect(self._on_validator_error, 
                           sender=validator_fsm, signal='error')
        dispatcher.connect(self._on_bill_in, 
                           sender=validator_fsm, signal='bill_in')
        dispatcher.connect(self.check_bill, 
                           sender=validator_fsm, signal='check_bill')

        dispatcher.connect(self._coin_amount_changed, 
                           sender=changer_fsm, signal='total_amount_changed')
        dispatcher.connect(self._bill_amount_changed, 
                           sender=validator_fsm, signal='total_amount_changed')
        dispatcher.connect(self._bill_count_changed, 
                           sender=validator_fsm, signal='bill_count_changed')

        # init parameters
        self._need_accept_amount = 0
        self._accepted_amount = 0
        self.accept_timeout_sec = 60

        self._acceptance_monitor_id = None

    def _after_started(self):
        self.changer_fsm.start()
        self.validator_fsm.start()

    def stop(self):
        self._stop_acceptance_monitor()
        self.changer_fsm.stop()
        self.validator_fsm.stop()

    def _on_changer_ready(self):
        self.changer_state = DEVICE_STATE_READY
        self.changer_ready()

    def _on_changer_offline(self):
        self.changer_state = DEVICE_STATE_OFFLINE
        self.changer_offline()

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

    def _on_coin_in(self, amount):
        self.coin_in(amount)
        self._fire_coin_in(amount)

    def _on_bill_in(self, amount):
        self.bill_in(amount)
        self._fire_bill_in(amount)

    def _is_ready(self):
        return ((self.changer_state == DEVICE_STATE_READY) and
                (self.validator_state == DEVICE_STATE_READY))

    def _after_ready(self):
        dispatcher.send_minimal(
            sender=self, signal='ready')

    def _dispense_amount(self, amount):
        self.changer_fsm.start_dispense(amount)

    def _ban_bill(self, amount):
        self.validator_fsm.ban_bill(amount)

    def _permit_bill(self, amount):
        self.validator_fsm.permit_bill(amount)

    def _start_accept(self, amount):
        self._start_acceptance_monitor()
        self._need_accept_amount = amount
        self._start_coin_accept()
        self._start_bill_accept()

    def _start_coin_accept(self, amount=0):
        self.changer_fsm.start_accept()

    def _start_bill_accept(self, amount=0):
        self.validator_fsm.start_accept()

    def _stop_accept(self):
        self.changer_fsm.stop_accept()
        self.validator_fsm.stop_accept()

    def _after_accept_timeout(self):
        self._stop_accept()
        if self._accepted_amount > 0:
            self.changer_fsm.start_dispense(self._accepted_amount)
        dispatcher.send_minimal(
            sender=self, signal='not_accepted')

    def _add_amount(self, amount):
        self._accepted_amount += amount
        self._reset_acceptance_monitor()
        self._deposit_amount_changed(self._accepted_amount)
        self._dispense_amount_changed(self.get_dispense_amount())

    def _amount_accepted(self, amount=0):
#         accepted_amount = self._accepted_amount + amount
        dispatcher.send_minimal(
            sender=self, signal='accepted', amount=self._accepted_amount)

    def _amount_dispensed(self, amount=0):
        dispatcher.send_minimal(
            sender=self, signal='dispensed', amount=amount)
        self._dispense_amount_changed(self.get_dispense_amount())

    def _is_enough(self, amount):
        return self._need_accept_amount <= self._accepted_amount + amount

    def _is_invalid_bill(self, amount):
        return not self._is_valid_bill(amount)

    def _is_valid_bill(self, amount):
        accepted_amount = self._accepted_amount + amount
        if not self.changer_fsm.can_dispense_amount(accepted_amount):
            return False
        change_amount = accepted_amount - self._need_accept_amount
        if (change_amount > 0 and 
            not self.changer_fsm.can_dispense_amount(change_amount)):
            return False
        return True

    def _is_valid_coin(self, amount):
        accepted_amount = self._accepted_amount + amount
        if accepted_amount <= self._need_accept_amount:
            return True
        change_amount = accepted_amount - self._need_accept_amount
        return self.changer_fsm.can_dispense_amount(change_amount)

    def _after_accept(self, amount):
        self._stop_acceptance_monitor()
        self._add_amount(amount)
        self._stop_accept()
        self._amount_accepted()

    def _dispense_all(self):
        dispensed_amount = self._accepted_amount
        self._accepted_amount = 0
        self._need_accept_amount = 0
        self._dispense_amount(dispensed_amount)

    def _dispense_change(self):
#         change_amount = self._accepted_amount - self._need_accept_amount
        change_amount = self.get_dispense_amount()
        self._accepted_amount = 0
        self._need_accept_amount = 0
        self._dispense_amount(change_amount)

    def _after_error(self, error_code, error_text):
        self._stop_acceptance_monitor()
        self._stop_accept()
        dispatcher.send_minimal(
            sender=self, signal='error', 
            error_code=error_code, error_text=error_text)

    def _start_acceptance_monitor(self):
        self._stop_acceptance_monitor()
        if self.accept_timeout_sec <= 0:
            return
        self._acceptance_monitor_id = reactor.callLater(self.accept_timeout_sec, self.accept_timeout) #@UndefinedVariable

    def _stop_acceptance_monitor(self):
        self._cancel_acceptance_monitor()
        self._acceptance_monitor_id = None

    def _reset_acceptance_monitor(self, amount=None):
        if self._acceptance_monitor_id is None:
            return
        self._cancel_acceptance_monitor()
        self._acceptance_monitor_id = reactor.callLater(self.accept_timeout_sec, self.accept_timeout) #@UndefinedVariable

    def _cancel_acceptance_monitor(self):
        if self._acceptance_monitor_id is None:
            return
        try:
            self._acceptance_monitor_id.cancel()
        except AlreadyCalled:
            pass

    #######################
    ## Public Methods
    #######################

    def get_dispense_amount(self):
        change_amount = self._accepted_amount - self._need_accept_amount
        return change_amount if change_amount > 0 else 0
    
    def get_deposit_amount(self):
        return self._accepted_amount

    def get_coin_amount(self):
        return self.changer_fsm.get_total_amount()

    def get_bill_amount(self):
        return self.validator_fsm.get_total_amount()

    def set_bill_amount(self, amount=0):
        return self.validator_fsm.set_total_amount(amount=amount)

    def get_total_amount(self):
        return self.get_coin_amount() + self.get_bill_amount()

    #######################
    ## Events
    #######################

    def _fire_coin_in(self, amount):
        dispatcher.send_minimal(
            sender=self, signal='coin_in', 
            amount=amount)

    def _fire_bill_in(self, amount):
        dispatcher.send_minimal(
            sender=self, signal='bill_in', 
            amount=amount)
    
    def _dispense_amount_changed(self, amount):
        dispatcher.send_minimal(
            sender=self, signal='dispense_amount_changed', 
            amount=amount)

    def _deposit_amount_changed(self, amount):
        dispatcher.send_minimal(
            sender=self, signal='deposit_amount_changed', 
            amount=amount)
        
    def _total_amount_changed(self, amount):
        dispatcher.send_minimal(
            sender=self, signal='total_amount_changed', 
            amount=amount)

    def _coin_amount_changed(self, amount):
        total_amount = amount + self.get_bill_amount()
        dispatcher.send_minimal(
            sender=self, signal='coin_amount_changed', 
            amount=amount)
        self._total_amount_changed(amount=total_amount)

    def _bill_amount_changed(self, amount):
        total_amount = amount + self.get_coin_amount()
        dispatcher.send_minimal(
            sender=self, signal='bill_amount_changed', 
            amount=amount)
        self._total_amount_changed(amount=total_amount)

    def _bill_count_changed(self, count):
        dispatcher.send_minimal(
            sender=self, signal='bill_count_changed', 
            count=count)
