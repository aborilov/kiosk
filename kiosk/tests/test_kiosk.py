from louie import dispatcher

from twisted.trial import unittest
from twisted.internet import reactor, defer, task

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from kiosk.fsm.kiosk_fsm import KioskFSM
from kiosk.fsm.changer_fsm import ChangerFSM
from kiosk.fsm.validator_fsm import BillValidatorFSM
from kiosk.fsm.cash_fsm import CashFSM

PRODUCT_1 = '1'
PRODUCT_2 = '2'
INVALID_PRODUCT = 'invalid_product'

PRODUCTS = {
            PRODUCT_1 : 10,
            PRODUCT_2 : 100
            }

class TestKioskMethods(unittest.TestCase):
    

    def setUp(self):
        self.fsm_listener = MagicMock()
        self.fsm_listener.total_amount_changed = \
                MagicMock(spec="total_amount_changed")
        self.fsm_listener.coin_amount_changed = \
                MagicMock(spec="coin_amount_changed")
        self.fsm_listener.bill_amount_changed = \
                MagicMock(spec="bill_amount_changed")
        self.fsm_listener.deposit_amount_changed = \
                MagicMock(spec="deposit_amount_changed")
        self.fsm_listener.dispense_amount_changed = \
                MagicMock(spec="dispense_amount_changed")
        self.fsm_listener.coin_in = \
                MagicMock(spec="coin_in")
        self.fsm_listener.bill_in = \
                MagicMock(spec="bill_in")
        
        self.plc = MagicMock()
        self.changer = MagicMock()
        self.changer.get_total_amount = MagicMock(return_value=0)

        self.validator = MagicMock()
        self.validator.get_total_amount = MagicMock(return_value=0)
        self.validator.set_total_amount = \
                MagicMock(spec="set_total_amount")
        
        self.changer_fsm = ChangerFSM(changer=self.changer)
        self.validator_fsm = BillValidatorFSM(validator=self.validator)
        self.cash_fsm = CashFSM(changer_fsm=self.changer_fsm, 
                                validator_fsm=self.validator_fsm)
        self.kiosk_fsm = KioskFSM(cash_fsm=self.cash_fsm, plc=self.plc, 
                                  products=PRODUCTS)
        
        dispatcher.connect(self.fsm_listener.total_amount_changed, 
                           sender=self.kiosk_fsm, 
                           signal='total_amount_changed')
        dispatcher.connect(self.fsm_listener.coin_amount_changed, 
                           sender=self.kiosk_fsm,
                           signal='coin_amount_changed')
        dispatcher.connect(self.fsm_listener.bill_amount_changed, 
                           sender=self.kiosk_fsm, 
                           signal='bill_amount_changed')
        dispatcher.connect(self.fsm_listener.deposit_amount_changed, 
                           sender=self.kiosk_fsm, 
                           signal='deposit_amount_changed')
        dispatcher.connect(self.fsm_listener.dispense_amount_changed, 
                           sender=self.kiosk_fsm, 
                           signal='dispense_amount_changed')
        dispatcher.connect(self.fsm_listener.coin_in, 
                           sender=self.kiosk_fsm, 
                           signal='coin_in')
        dispatcher.connect(self.fsm_listener.bill_in, 
                           sender=self.kiosk_fsm, 
                           signal='bill_in')

        self.kiosk_fsm.start()
        

    def tearDown(self):
        self.kiosk_fsm.stop()

    @defer.inlineCallbacks
    def test_get_deposit_amount(self):
        '''
        check that method kiosk_fsm.get_deposit_amount() return
        actual deposit amount during product payment
        '''
        self.assertEquals(0, self.kiosk_fsm.get_deposit_amount())
        
        self.set_kiosk_ready_state()
        self.assertEquals(0, self.kiosk_fsm.get_deposit_amount())
        
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.assertEquals(0, self.kiosk_fsm.get_deposit_amount())
        
        self.accept_coin_amount(1)
        self.assertEquals(1, self.kiosk_fsm.get_deposit_amount())

        self.accept_coin_amount(2)
        self.assertEquals(3, self.kiosk_fsm.get_deposit_amount())

        self.accept_bill_amount(1)
        yield self.sleep_defer(sleep_sec=0.1)
        self.assertEquals(4, self.kiosk_fsm.get_deposit_amount())

        self.accept_bill_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)
        self.assertEquals(7, self.kiosk_fsm.get_deposit_amount())
        
        self.accept_bill_amount(PRODUCTS[product] - 6)
        yield self.sleep_defer(sleep_sec=0.1)
        self.assertEquals(PRODUCTS[product] + 1, 
                          self.kiosk_fsm.get_deposit_amount())
        
        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)

        self.fire_coin_out(1)
        self.assertEquals(0, self.kiosk_fsm.get_deposit_amount())

    @defer.inlineCallbacks
    def test_get_dispense_amount_1(self):
        '''
        check that method kiosk_fsm.get_dispense_amount() return
        actual dispensed amount during product payment
        '''
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
        
        self.set_kiosk_ready_state()
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
        
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
        
        self.accept_coin_amount(1)
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())

        self.accept_bill_amount(2)
        yield self.sleep_defer(sleep_sec=0.1)
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())

        self.accept_coin_amount(PRODUCTS[product] - 4)
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
        
        self.accept_coin_amount(1)
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
        
        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)

        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
            
    @defer.inlineCallbacks
    def test_get_dispense_amount_2(self):
        '''
        check that method kiosk_fsm.get_dispense_amount() return
        actual dispensed amount during product payment
        '''
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
        
        self.set_kiosk_ready_state()
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
        
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
        
        self.accept_bill_amount(PRODUCTS[product] + 1)
        yield self.sleep_defer(sleep_sec=0.1)
        self.assertEquals(1, self.kiosk_fsm.get_dispense_amount())

        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)

        self.fire_coin_out(1)

        self.assertEquals(0, self.kiosk_fsm.get_dispense_amount())
        
    def test_get_coin_amount(self):
        self.changer.get_total_amount.return_value = 0
        self.assertEquals(0, self.kiosk_fsm.get_coin_amount())

        self.changer.get_total_amount.return_value = 1
        self.assertEquals(1, self.kiosk_fsm.get_coin_amount())

        self.changer.get_total_amount.return_value = 10
        self.assertEquals(10, self.kiosk_fsm.get_coin_amount())
    
    def test_get_bill_amount(self):
        self.validator.get_total_amount.return_value = 0
        self.assertEquals(0, self.kiosk_fsm.get_bill_amount())

        self.validator.get_total_amount.return_value = 1
        self.assertEquals(1, self.kiosk_fsm.get_bill_amount())

        self.validator.get_total_amount.return_value = 10
        self.assertEquals(10, self.kiosk_fsm.get_bill_amount())
    
    def test_get_total_amount(self):
        self.changer.get_total_amount.return_value = 0
        self.validator.get_total_amount.return_value = 0
        self.assertEquals(0, self.kiosk_fsm.get_total_amount())

        self.changer.get_total_amount.return_value = 1
        self.validator.get_total_amount.return_value = 0
        self.assertEquals(1, self.kiosk_fsm.get_total_amount())
        
        self.changer.get_total_amount.return_value = 0
        self.validator.get_total_amount.return_value = 1
        self.assertEquals(1, self.kiosk_fsm.get_total_amount())

        self.changer.get_total_amount.return_value = 1
        self.validator.get_total_amount.return_value = 1
        self.assertEquals(2, self.kiosk_fsm.get_total_amount())

        self.changer.get_total_amount.return_value = 5
        self.validator.get_total_amount.return_value = 6
        self.assertEquals(11, self.kiosk_fsm.get_total_amount())

    def test_set_bill_amount(self):
        self.assertEquals([], 
                self.validator.set_total_amount.call_args_list)
        
        self.kiosk_fsm.set_bill_amount(amount=0)
        self.assertEquals([({'amount':0,},)], 
                self.validator.set_total_amount.call_args_list)
        self.validator.set_total_amount.reset_mock()
        
        self.kiosk_fsm.set_bill_amount(amount=1)
        self.assertEquals([({'amount':1,},)], 
                self.validator.set_total_amount.call_args_list)
        self.validator.set_total_amount.reset_mock()

        self.kiosk_fsm.set_bill_amount(amount=10)
        self.assertEquals([({'amount':10,},)], 
                self.validator.set_total_amount.call_args_list)

    @defer.inlineCallbacks
    def test_amount_deposited(self):
        self.assertEquals([], 
                self.fsm_listener.deposit_amount_changed.call_args_list)
        
        self.set_kiosk_ready_state()
        self.assertEquals([], 
                self.fsm_listener.deposit_amount_changed.call_args_list)
        
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.assertEquals([], 
                self.fsm_listener.deposit_amount_changed.call_args_list)

        self.accept_coin_amount(1)
        self.assertEquals([({'amount':1,},)], 
                self.fsm_listener.deposit_amount_changed.call_args_list)
        self.fsm_listener.deposit_amount_changed.reset_mock()
        
        self.accept_bill_amount(PRODUCTS[product])
        yield self.sleep_defer(sleep_sec=0.1)
        self.assertEquals([({'amount':PRODUCTS[product] + 1,},)], 
                self.fsm_listener.deposit_amount_changed.call_args_list)
        self.fsm_listener.deposit_amount_changed.reset_mock()

        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)

        self.fire_coin_out(1)

        self.assertEquals([], 
                self.fsm_listener.deposit_amount_changed.call_args_list)

    @defer.inlineCallbacks
    def test_amount_dispensed_1(self):
        '''
        check 'dispense_amount_changed' notification when exact amount accepted
        '''
        self.assertEquals([], 
                self.fsm_listener.dispense_amount_changed.call_args_list)
        
        self.set_kiosk_ready_state()
        self.assertEquals([], 
                self.fsm_listener.dispense_amount_changed.call_args_list)
        
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.assertEquals([], 
                self.fsm_listener.dispense_amount_changed.call_args_list)

        self.accept_coin_amount(1)
        self.assertEquals([({'amount':0,},)], 
                self.fsm_listener.dispense_amount_changed.call_args_list)
        self.fsm_listener.dispense_amount_changed.reset_mock()
        
        self.accept_bill_amount(PRODUCTS[product] - 1)
        yield self.sleep_defer(sleep_sec=0.1)
        self.assertEquals([({'amount':0,},)], 
                self.fsm_listener.dispense_amount_changed.call_args_list)
        self.fsm_listener.dispense_amount_changed.reset_mock()

        self.product_prepared()

        self.assertEquals([], 
                self.fsm_listener.dispense_amount_changed.call_args_list)

    @defer.inlineCallbacks
    def test_amount_dispensed_2(self):
        '''
        check 'dispense_amount_changed' notification when more amount accepted
        '''
        self.assertEquals([], 
                self.fsm_listener.dispense_amount_changed.call_args_list)
        
        self.set_kiosk_ready_state()
        self.assertEquals([], 
                self.fsm_listener.dispense_amount_changed.call_args_list)
        
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.assertEquals([], 
                self.fsm_listener.dispense_amount_changed.call_args_list)

        self.accept_coin_amount(1)
        self.assertEquals([({'amount':0,},)], 
                self.fsm_listener.dispense_amount_changed.call_args_list)
        self.fsm_listener.dispense_amount_changed.reset_mock()
        
        self.accept_bill_amount(PRODUCTS[product])
        yield self.sleep_defer(sleep_sec=0.1)
        self.assertEquals([({'amount':1,},)], 
                self.fsm_listener.dispense_amount_changed.call_args_list)
        self.fsm_listener.dispense_amount_changed.reset_mock()

        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)

        self.fire_coin_out(1)

        self.assertEquals([({'amount':0,},)], 
                self.fsm_listener.dispense_amount_changed.call_args_list)
            
    def test_total_amount_changed(self):
        self.changer.get_total_amount.return_value = 0
        self.validator.get_total_amount.return_value = 0
        
        self.assertEquals([], 
                self.fsm_listener.total_amount_changed.call_args_list)

        self.changer.get_total_amount.return_value = 1
        self.validator.get_total_amount.return_value = 0
        self.assertEquals([], 
                self.fsm_listener.total_amount_changed.call_args_list)
        
        self.accept_coin_amount()
        self.assertEquals([({'amount':1,},)], 
                self.fsm_listener.total_amount_changed.call_args_list)
        self.fsm_listener.total_amount_changed.reset_mock()
        
        self.changer.get_total_amount.return_value = 0
        self.validator.get_total_amount.return_value = 1
        self.assertEquals([], 
                self.fsm_listener.total_amount_changed.call_args_list)
        
        self.fire_bill_in()
        self.assertEquals([({'amount':1,},)], 
                self.fsm_listener.total_amount_changed.call_args_list)
        self.fsm_listener.total_amount_changed.reset_mock()

        self.changer.get_total_amount.return_value = 1
        self.validator.get_total_amount.return_value = 1
        self.assertEquals([], 
                self.fsm_listener.total_amount_changed.call_args_list)
        
        self.accept_coin_amount()
        self.assertEquals([({'amount':2,},)], 
                self.fsm_listener.total_amount_changed.call_args_list)
        self.fsm_listener.total_amount_changed.reset_mock()

        self.changer.get_total_amount.return_value = 5
        self.validator.get_total_amount.return_value = 6
        self.assertEquals([], 
                self.fsm_listener.total_amount_changed.call_args_list)
        
        self.fire_bill_in()
        self.assertEquals([({'amount':11,},)], 
                self.fsm_listener.total_amount_changed.call_args_list)
    
    def test_coin_amount_changed(self):
        self.changer.get_total_amount.return_value = 0
        
        self.assertEquals([], 
                self.fsm_listener.coin_amount_changed.call_args_list)

        self.changer.get_total_amount.return_value = 1
        self.assertEquals([], 
                self.fsm_listener.coin_amount_changed.call_args_list)
        
        self.accept_coin_amount()
        self.assertEquals([({'amount':1,},)], 
                self.fsm_listener.coin_amount_changed.call_args_list)
        self.fsm_listener.coin_amount_changed.reset_mock()
        
        self.changer.get_total_amount.return_value = 5
        self.assertEquals([], 
                self.fsm_listener.coin_amount_changed.call_args_list)
        
        self.accept_coin_amount()
        self.assertEquals([({'amount':5,},)], 
                self.fsm_listener.coin_amount_changed.call_args_list)
    
    def test_bill_amount_changed(self):
        self.validator.get_total_amount.return_value = 0
        
        self.assertEquals([], 
                self.fsm_listener.bill_amount_changed.call_args_list)

        self.validator.get_total_amount.return_value = 1
        self.assertEquals([], 
                self.fsm_listener.bill_amount_changed.call_args_list)
        
        self.fire_bill_in()
        self.assertEquals([({'amount':1,},)], 
                self.fsm_listener.bill_amount_changed.call_args_list)
        self.fsm_listener.bill_amount_changed.reset_mock()
        
        self.validator.get_total_amount.return_value = 5
        self.assertEquals([], 
                self.fsm_listener.bill_amount_changed.call_args_list)
        
        self.fire_bill_in()
        self.assertEquals([({'amount':5,},)], 
                self.fsm_listener.bill_amount_changed.call_args_list)

    def test_coin_in(self):
        self.set_kiosk_ready_state()
        
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=5)

        self.assertEquals([({'amount':1,},), ({'amount':5,},)], 
                self.fsm_listener.coin_in.call_args_list)
        self.assertEquals([], 
                self.fsm_listener.bill_in.call_args_list)

    def test_bill_in(self):
        self.set_kiosk_ready_state()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='bill_in', amount=1)
        dispatcher.send_minimal(
            sender=self.validator, signal='bill_in', amount=5)

        self.assertEquals([({'amount':1,},), ({'amount':5,},)], 
                self.fsm_listener.bill_in.call_args_list)
        self.assertEquals([], 
                self.fsm_listener.coin_in.call_args_list)
        
    def set_kiosk_ready_state(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator, signal='online')
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')

    def accept_coin_amount(self, amount=0):
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=amount)

    def fire_coin_out(self, amount=0):
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=amount)

    def accept_bill_amount(self, amount):
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=amount)
        self.fire_bill_in(amount=amount)

    def fire_bill_in(self, amount=0):
        dispatcher.send_minimal(
            sender=self.validator, signal='bill_in', amount=amount)
        
    def product_prepared(self):
        dispatcher.send_minimal(
            sender=self.plc, signal='prepared')

    def product_not_prepared(self):
        dispatcher.send_minimal(
            sender=self.plc, signal='not_prepared')

    def sleep_defer(self, sleep_sec):
        return task.deferLater(reactor, sleep_sec, defer.passthru, None)

