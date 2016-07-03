import logging

from louie import dispatcher
from transitions import Machine

logger = logging.getLogger('kiosk')

class KioskFSM(Machine):

    def __init__(self, plc, cash_fsm, products):

        states = ["init", "wait_ready", "error", "ready",
                  "start_sell", "start_prepare", "start_dispense"]
        transitions = [
            # trigger,                   source,            dest,              conditions,          unless,              before,             after
            ['start',                    'init',            'wait_ready',       None,                None,                None,              '_after_started'        ],
            ['cash_fsm_ready',           'wait_ready',      'ready',            None,                None,                None,              '_after_ready'          ],
            ['sell',                     'ready',           'ready',            None,                '_is_valid_product', None,              '_reset_sell'           ],
            ['sell',                     'ready',           'start_sell',       '_is_valid_product', None,                None,              '_start_sell'           ],
            ['amount_not_accepted',      'start_sell',      'ready',            None,                None,                None,              '_reset_sell'           ],
            ['amount_accepted',          'start_sell',      'start_prepare',    None,                None,                None,              '_prepare'              ],
            ['not_prepared',             'start_prepare',   'start_dispense',   None,                None,                None,              '_dispense_all'         ],
            ['prepared',                 'start_prepare',   'start_dispense',   None,                None,                None,              '_dispense_change'      ],
            ['amount_dispensed',         'start_dispense',  'ready',            None,                None,                None,              '_after_ready'          ],

            ['cash_fsm_error',           'ready',           'error',            None,                None,                '_dispense_all',   '_after_error'          ],
            ['cash_fsm_error',           'start_sell',      'error',            None,                None,                '_dispense_all',   '_after_error'          ],
            ['cash_fsm_error',           'start_prepare',   'error',            None,                None,                '_dispense_change','_after_error'          ],
            ['cash_fsm_error',           'start_dispense',  'error',            None,                None,                None,              '_after_error'          ],

        ]
        super(KioskFSM, self).__init__(
            states=states, 
            transitions=transitions, 
            initial='init', 
            ignore_invalid_triggers=True)

        self.plc = plc
        self.cash_fsm = cash_fsm
        self.products = products

        dispatcher.connect(self.cash_fsm_error, sender=cash_fsm, signal='error')
        dispatcher.connect(self.cash_fsm_ready, sender=cash_fsm, signal='ready')
        dispatcher.connect(self.amount_not_accepted, 
                           sender=cash_fsm, signal='not_accepted')
        dispatcher.connect(self.amount_accepted, 
                           sender=cash_fsm, signal='accepted')
        dispatcher.connect(self.amount_dispensed, 
                           sender=cash_fsm, signal='dispensed')
        dispatcher.connect(self.prepared, sender=plc, signal='prepared')
        dispatcher.connect(self.not_prepared, sender=plc, signal='not_prepared')

        dispatcher.connect(self._dispense_amount_changed, 
                           sender=cash_fsm, signal='dispense_amount_changed')
        dispatcher.connect(self._deposit_amount_changed, 
                           sender=cash_fsm, signal='deposit_amount_changed')
        dispatcher.connect(self._total_amount_changed, 
                           sender=cash_fsm, signal='total_amount_changed')
        dispatcher.connect(self._coin_amount_changed, 
                           sender=cash_fsm, signal='coin_amount_changed')
        dispatcher.connect(self._bill_amount_changed, 
                           sender=cash_fsm, signal='bill_amount_changed')
        dispatcher.connect(self._bill_count_changed, 
                           sender=cash_fsm, signal='bill_count_changed')

        # init parameters
        self._product = -1

    def _after_started(self):
        self.cash_fsm.start()

    def stop(self):
        # TODO reset FSM
        self.cash_fsm.stop()

    def _after_ready(self, amount=0):
        logger.debug("_after_ready")
        dispatcher.send_minimal(
            sender=self, signal='ready')

    def _is_valid_product(self, product):
        return product in self.products

    def _start_sell(self, product):
        self._product = product
        amount = self.products[product]
        self.cash_fsm.accept(amount)

    def _reset_sell(self, product=-1):
        dispatcher.send_minimal(
            sender=self, signal='reset_sell')
        self._after_ready()

    def _prepare(self, amount=-1):
        self.plc.prepare(self._product)

    def _dispense_all(self, error_code=0, error_text=''):
        self.cash_fsm.dispense_all()

    def _dispense_change(self, error_code=0, error_text=''):
        self.cash_fsm.dispense_change()

    def _after_error(self, error_code, error_text):
        dispatcher.send_minimal(
            sender=self, signal='error', 
            error_code=error_code, error_text=error_text)

    #######################
    ## Public Methods
    #######################
    def get_dispense_amount(self):
        return self.cash_fsm.get_dispense_amount()
    
    def get_deposit_amount(self):
        return self.cash_fsm.get_deposit_amount()

    def get_coin_amount(self):
        return self.cash_fsm.get_coin_amount()

    def get_bill_amount(self):
        return self.cash_fsm.get_bill_amount()

    def get_total_amount(self):
        return self.cash_fsm.get_total_amount()

    def set_bill_amount(self, amount=0):
        return self.cash_fsm.set_bill_amount(amount=amount)

    #######################
    ## Events
    #######################
    
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
        dispatcher.send_minimal(
            sender=self, signal='coin_amount_changed', 
            amount=amount)

    def _bill_amount_changed(self, amount):
        dispatcher.send_minimal(
            sender=self, signal='bill_amount_changed', 
            amount=amount)

    def _bill_count_changed(self, count):
        dispatcher.send_minimal(
            sender=self, signal='bill_count_changed', 
            count=count)
