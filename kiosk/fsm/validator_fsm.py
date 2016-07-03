import logging

from twisted.internet import reactor

from louie import dispatcher
from transitions import Machine


logger = logging.getLogger('kiosk')

class BillValidatorFSM(Machine):

    def __init__(self, validator):

        states = ["offline", "online", "error", "ready",
                  "wait_bill", "bill_confirm"]
        transitions = [
            # trigger,                 source,            dest,              conditions,     unless,          before,           after
            ['online',                 'offline',         'online',           None,           None,            None,            '_after_online'     ],
            ['initialized',            'online',          'ready',            None,           None,            None,            '_after_init'       ],
            ['start_accept',           'ready',           'wait_bill',        None,           None,            None,            '_start_accept'     ],
            ['check_bill',             'wait_bill',       'bill_confirm',     None,           None,            None,            '_check_bill'       ],
            ['stop_accept',            'wait_bill',       'ready',            None,           None,            None,             None               ],
            ['ban_bill',               'bill_confirm',    'ready',            None,           None,           '_ban_bill',       None               ],
            ['permit_bill',            'bill_confirm',    'ready',            None,           None,           '_permit_bill',    None               ],

            ['check_bill',             'ready',           'ready',            None,           None,           '_ban_bill',       None               ],
            ['check_bill',             'error',           'error',            None,           None,           '_ban_bill',       None               ],

            ['error',                  'online',          'error',            None,           None,            None,            '_after_error'      ],
            ['error',                  'ready',           'error',            None,           None,            None,            '_after_error'      ],
            ['error',                  'wait_bill',       'error',            None,           None,            None,            '_after_error'      ],
            ['error',                  'bill_confirm',    'error',            None,           None,            None,            '_after_error'      ],
            ['offline',                'online',          'offline',          None,           None,            None,            '_after_offline'    ],
            ['offline',                'ready',           'offline',          None,           None,            None,            '_after_offline'    ],
            ['offline',                'error',           'offline',          None,           None,            None,            '_after_offline'    ],
            ['offline',                'wait_bill',       'offline',          None,           None,            None,            '_after_offline'    ],
            ['offline',                'bill_confirm',    'offline',          None,           None,            None,            '_after_offline'    ],
        ]
        super(BillValidatorFSM, self).__init__(
            states=states, 
            transitions=transitions, 
            initial='offline', 
            ignore_invalid_triggers=True)
        self.validator = validator
        dispatcher.connect(self.online, sender=validator, signal='online')
        dispatcher.connect(self.initialized, 
                           sender=validator, signal='initialized')
        dispatcher.connect(self.error, sender=validator, signal='error')
        dispatcher.connect(self.offline, sender=validator, signal='offline')
        dispatcher.connect(self.check_bill, 
                           sender=validator, signal='check_bill')
        dispatcher.connect(self.bill_in, 
                           sender=validator, signal='bill_in')

        self._accepted_amount = 0

    def start(self):
        self.validator.start_device()

    def stop(self):
        self.validator.stop_device()

    def _after_online(self):
        dispatcher.send_minimal(
            sender=self, signal='online')

    def _after_offline(self):
        dispatcher.send_minimal(
            sender=self, signal='offline')

    def _after_init(self):
        self._start_accept()
        dispatcher.send_minimal(
            sender=self, signal='initialized')

    def _after_error(self, error_code, error_text):
        self._stop_accept()
        self.validator.return_bill()
        dispatcher.send_minimal(
            sender=self, signal='error', 
            error_code=error_code, error_text=error_text)

    def _check_bill(self, amount):
        self._accepted_amount = amount
        dispatcher.send_minimal(
            sender=self, signal='check_bill', amount=amount)

    def _start_accept(self):
        logger.debug("_start_accept")
        self.validator.start_accept()

    def _stop_accept(self):
        logger.debug("_stop_accept")
        self.validator.stop_accept()


    def _ban_bill(self, amount=0):
        #TODO wait until bill returned. 
        #Maybe need to add a new FSM state return_bill
        self.validator.return_bill()

    def _permit_bill(self, amount=0):
        #TODO wait until bill accepted. 
        #Maybe need to add a new FSM state accept_bill
        self.validator.stack_bill()


#     def _fire_bill_in(self, amount=0):
#         reactor.callLater(0, self._fire_bill_in_impl, amount=amount) #@UndefinedVariable

    def bill_in(self, amount=0):
        dispatcher.send_minimal(sender=self, signal='bill_in', amount=amount)
        self._total_amount_changed(self.get_total_amount())
        self._bill_count_changed(self.get_bill_count())
#             sender=self, signal='bill_in', amount=self._accepted_amount)

    #######################
    ## Public Methods
    #######################

    def get_total_amount(self):
        return self.validator.get_total_amount()
    
    def set_total_amount(self, amount=0):
        return self.validator.set_total_amount(amount=amount)

    def get_bill_count(self):
        return self.validator.get_bill_count()

    #######################
    ## Events
    #######################
    
    def _total_amount_changed(self, amount):
        dispatcher.send_minimal(
            sender=self, signal='total_amount_changed', 
            amount=amount)

    def _bill_count_changed(self, count):
        dispatcher.send_minimal(
            sender=self, signal='bill_count_changed', 
            count=count)
