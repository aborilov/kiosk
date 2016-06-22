from louie import dispatcher

from twisted.internet import reactor, defer, task

#from unittest import TestCase
from twisted.trial import unittest

from kiosk.fsm.kiosk_fsm import KioskFSM
from kiosk.fsm.changer_fsm import ChangerFSM
from kiosk.fsm.validator_fsm import BillValidatorFSM
from kiosk.fsm.cash_fsm import CashFSM


try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock


PRODUCT_1 = '1'
PRODUCT_2 = '2'
INVALID_PRODUCT = 'invalid_product'

PRODUCTS = {
            PRODUCT_1 : 10,
            PRODUCT_2 : 100
            }

class TestKioskFsm(unittest.TestCase):
    

    def setUp(self):
        self.fsm_listener = MagicMock()
        self.fsm_listener.ready = MagicMock(spec="ready")
        self.fsm_listener.reset_sell = MagicMock(spec="reset_sell")
        self.fsm_listener.error = MagicMock(spec="error")
        
        self.plc = MagicMock()
        self.plc.prepare = MagicMock()
        
        self.changer = MagicMock()
        self.changer.start_accept = MagicMock()
        self.changer.stop_accept = MagicMock()
        self.changer.dispense_amount = MagicMock()
        self.changer.can_dispense_amount = MagicMock(return_value=True)

        self.validator = MagicMock()
        self.validator.start_accept = MagicMock()
        self.validator.stop_accept = MagicMock()
        self.validator.stack_bill = MagicMock()
        self.validator.return_bill = MagicMock()
        
        self.changer_fsm = ChangerFSM(changer=self.changer)
        self.validator_fsm = BillValidatorFSM(validator=self.validator)
        self.cash_fsm = CashFSM(changer_fsm=self.changer_fsm, validator_fsm=self.validator_fsm)
        self.kiosk_fsm = KioskFSM(cash_fsm=self.cash_fsm, plc=self.plc, products=PRODUCTS)
        
        dispatcher.connect(self.fsm_listener.ready, sender=self.kiosk_fsm, signal='ready')
        dispatcher.connect(self.fsm_listener.reset_sell, sender=self.kiosk_fsm, signal='reset_sell')
        dispatcher.connect(self.fsm_listener.error, sender=self.kiosk_fsm, signal='error')

        self.kiosk_fsm.start()
        

    def tearDown(self):
        self.kiosk_fsm.stop()


    def test_ready_state(self):
        self.set_kiosk_ready_state()
        self.check_outputs(fsm_ready_expected_args_list=[()],
                           validator_start_accept_expected_args_list=[()])


    def test_select_product(self):
        self.set_kiosk_ready_state()
        self.reset_outputs()

        self.kiosk_fsm.sell(product=PRODUCT_1)
        self.check_outputs(changer_start_accept_expected_args_list=[()],
                           validator_start_accept_expected_args_list=[()])
        
        
    def test_scenarious_1_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins on the exact amount
        4) Prepare product
        5) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)

        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-6)
        self.accept_coin_amount(6)
        self.check_outputs(changer_start_accept_expected_args_list=[()],
                           changer_stop_accept_expected_args_list=[(), ()],
                           plc_prepare_expected_args_list=[((PRODUCT_1,),)])
        self.reset_outputs()
        #4
        self.product_prepared()
        self.check_outputs()


    @defer.inlineCallbacks
    def test_scenarious_1_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of bills on the exact amount
        4) Prepare product
        5) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)

        self.reset_outputs()
        #3
        self.accept_bill_amount(PRODUCTS[product]-6)
        yield self.sleep_defer(sleep_sec=0.5)
        self.accept_bill_amount(6)
        yield self.sleep_defer(sleep_sec=0.5)
        
        self.check_outputs(plc_prepare_expected_args_list=[((PRODUCT_1,),)],
                           changer_stop_accept_expected_args_list=[()],
                           validator_start_accept_expected_args_list=[()],
                           validator_stack_bill_expected_args_list=[(), ()])
        self.reset_outputs()
        #4
        self.product_prepared()
        self.check_outputs()
        

    @defer.inlineCallbacks
    def test_scenarious_1_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins and bills on the exact amount
        4) Prepare product
        5) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)

        self.reset_outputs()
        #3
        self.accept_coin_amount(PRODUCTS[product]-6)
        self.accept_bill_amount(6)
        yield self.sleep_defer(sleep_sec=0.5)
        
        self.check_outputs(plc_prepare_expected_args_list=[((PRODUCT_1,),)],
                           changer_start_accept_expected_args_list=[()],
                           changer_stop_accept_expected_args_list=[(), ()],
                           validator_stack_bill_expected_args_list=[()])
        self.reset_outputs()
        #4
        self.product_prepared()
        self.check_outputs()


    @defer.inlineCallbacks
    def test_scenarious_2_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins on the more amount
        4) Prepare product
        5) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)

        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-6)
        self.accept_coin_amount(7)
        self.check_outputs(changer_start_accept_expected_args_list=[()],
                           changer_stop_accept_expected_args_list=[(), ()],
                           plc_prepare_expected_args_list=[((PRODUCT_1,),)])
        self.reset_outputs()
        #4
        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=1)
        
        self.check_outputs(changer_dispense_amount_expected_args_list=[((1,),)])


    @defer.inlineCallbacks
    def test_scenarious_2_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of bills on the more amount
        4) Prepare product
        5) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)

        self.reset_outputs()
        #3
        self.accept_bill_amount(PRODUCTS[product]-6)
        yield self.sleep_defer(sleep_sec=0.5)
        self.accept_bill_amount(7)
        yield self.sleep_defer(sleep_sec=0.5)
        
        self.check_outputs(plc_prepare_expected_args_list=[((PRODUCT_1,),)],
                           changer_stop_accept_expected_args_list=[()],
                           validator_start_accept_expected_args_list=[()],
                           validator_stack_bill_expected_args_list=[(), ()])
        self.reset_outputs()
        #4

        self.product_prepared()

        yield self.sleep_defer(sleep_sec=1)
        
        self.check_outputs(changer_dispense_amount_expected_args_list=[((1,),)])
        

    @defer.inlineCallbacks
    def test_scenarious_2_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins and bills on the more amount
        4) Prepare product
        5) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)

        self.reset_outputs()
        #3
        self.accept_coin_amount(PRODUCTS[product]-6)
        self.accept_bill_amount(7)
        yield self.sleep_defer(sleep_sec=0.5)
        
        self.check_outputs(plc_prepare_expected_args_list=[((PRODUCT_1,),)],
                           changer_start_accept_expected_args_list=[()],
                           changer_stop_accept_expected_args_list=[(), ()],
                           validator_stack_bill_expected_args_list=[()])
        self.reset_outputs()
        #4
        self.product_prepared()

        yield self.sleep_defer(sleep_sec=1)
        
        self.check_outputs(changer_dispense_amount_expected_args_list=[((1,),)])

        
    def set_kiosk_ready_state(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator, signal='online')
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')

    
    def accept_coin_amount(self, amount):
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=amount)


    def accept_bill_amount(self, amount):
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=amount)
        
        
    def product_prepared(self):
        dispatcher.send_minimal(
            sender=self.plc, signal='prepared')

        
        
    def reset_outputs(self):
        self.fsm_listener.ready.reset_mock()
        self.fsm_listener.reset_sell.reset_mock()
        self.fsm_listener.error.reset_mock()

        self.plc.prepare.reset_mock()
        
        self.changer.start_accept.reset_mock()
        self.changer.stop_accept.reset_mock()
        self.changer.dispense_amount.reset_mock()

        self.validator.start_accept.reset_mock()
        self.validator.stop_accept.reset_mock()
        self.validator.stack_bill.reset_mock()
        self.validator.return_bill.reset_mock()
        
                      
        
    def check_outputs(self,
                      fsm_ready_expected_args_list=[],
                      fsm_reset_sell_expected_args_list=[],
                      fsm_error_expected_args_list=[],
                      changer_start_accept_expected_args_list=[],
                      changer_stop_accept_expected_args_list=[],
                      changer_dispense_amount_expected_args_list=[],
                      validator_start_accept_expected_args_list=[],
                      validator_stop_accept_expected_args_list=[],
                      validator_stack_bill_expected_args_list=[],
                      validator_return_bill_expected_args_list=[],
                      plc_prepare_expected_args_list=[]):
        
        self.assertEquals(fsm_ready_expected_args_list, self.fsm_listener.ready.call_args_list)
        self.assertEquals(fsm_reset_sell_expected_args_list, self.fsm_listener.reset_sell.call_args_list)
        self.assertEquals(fsm_error_expected_args_list, self.fsm_listener.error.call_args_list)
        self.assertEquals(changer_start_accept_expected_args_list, self.changer.start_accept.call_args_list)
        self.assertEquals(changer_stop_accept_expected_args_list, self.changer.stop_accept.call_args_list)
        self.assertEquals(changer_dispense_amount_expected_args_list, self.changer.dispense_amount.call_args_list)
        self.assertEquals(validator_start_accept_expected_args_list, self.validator.start_accept.call_args_list)
        self.assertEquals(validator_stop_accept_expected_args_list, self.validator.stop_accept.call_args_list)
        self.assertEquals(validator_stack_bill_expected_args_list, self.validator.stack_bill.call_args_list)
        self.assertEquals(validator_return_bill_expected_args_list, self.validator.return_bill.call_args_list)
        self.assertEquals(plc_prepare_expected_args_list, self.plc.prepare.call_args_list)


    def sleep_defer(self, sleep_sec):
        return task.deferLater(reactor, sleep_sec, defer.passthru, None)
