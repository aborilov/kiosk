from louie import dispatcher

from twisted.internet import reactor, defer, task

#from unittest import TestCase
from twisted.trial import unittest

from kiosk.fsm.kiosk_fsm import KioskFSM
from kiosk.fsm.changer_fsm import ChangerFSM
from kiosk.fsm.validator_fsm import BillValidatorFSM
from kiosk.fsm.cash_fsm import CashFSM

from pymdb.device import changer

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
        self.cash_fsm = CashFSM(changer_fsm=self.changer_fsm, 
                                validator_fsm=self.validator_fsm)
        self.kiosk_fsm = KioskFSM(cash_fsm=self.cash_fsm, plc=self.plc, 
                                  products=PRODUCTS)
        
        dispatcher.connect(self.fsm_listener.ready, 
                           sender=self.kiosk_fsm, signal='ready')
        dispatcher.connect(self.fsm_listener.reset_sell, 
                           sender=self.kiosk_fsm, signal='reset_sell')
        dispatcher.connect(self.fsm_listener.error, 
                           sender=self.kiosk_fsm, signal='error')

        self.kiosk_fsm.start()
        

    def tearDown(self):
        self.kiosk_fsm.stop()


    def test_ready_state(self):
        self.set_kiosk_ready_state()
        self.check_outputs(fsm_ready_expected=[()],
                           validator_start_accept_expected=[()])


    def test_select_product(self):
        self.set_kiosk_ready_state()
        self.reset_outputs()

        self.kiosk_fsm.sell(product=PRODUCT_1)
        self.check_outputs(changer_start_accept_expected=[()],
                           validator_start_accept_expected=[()])
        
    
    @defer.inlineCallbacks
    def test_scenarious_1_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins on enough amount
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
        self.check_outputs(changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[()])
        
        self.accept_coin_amount(6)
        self.check_outputs(changer_stop_accept_expected=[()],
                           plc_prepare_expected=[((PRODUCT_1,),)])
        
        #4
        self.product_prepared()
        
        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_1_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of bills on enough amount
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
        self.check_bill_amount(PRODUCTS[product]-6)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(validator_start_accept_expected=[()],
                           validator_stack_bill_expected=[()])
        
        self.check_bill_amount(6)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_stop_accept_expected=[()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()
        
        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(fsm_ready_expected=[()])
        

    @defer.inlineCallbacks
    def test_scenarious_1_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins and bills on enough amount
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
        self.check_outputs(changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[()])
        
        self.check_bill_amount(6)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_stop_accept_expected=[()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()
        
        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_2_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins on more amount
        4) Prepare product
        5) Dispense change
        6) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-6)
        self.reset_outputs()
        
        self.accept_coin_amount(7)
        self.check_outputs(changer_stop_accept_expected=[()],
                           plc_prepare_expected=[((PRODUCT_1,),)])
        
        #4
        self.product_prepared()
        
        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_coin_out(1)
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_2_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of bills on more amount
        4) Prepare product
        5) Dispense change
        6) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.check_bill_amount(PRODUCTS[product]-6)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()
        
        self.check_bill_amount(7)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_stop_accept_expected=[()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()
        
        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])
        
        #6
        self.fire_coin_out(1)
        self.check_outputs(fsm_ready_expected=[()])

        

    @defer.inlineCallbacks
    def test_scenarious_2_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins and bills on more amount
        4) Prepare product
        5) Dispense change
        6) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-6)
        self.reset_outputs()

        self.check_bill_amount(7)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_stop_accept_expected=[()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()
        
        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_coin_out(1)
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_3_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins on a lower amount
        4) Wait accept timeout
        5) Return coins on accepted amount
        6) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.2
        
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-6)
        self.reset_outputs()
        
        self.accept_coin_amount(5)
        
        #4
        yield self.sleep_defer(sleep_sec=0.5)
        
        #5
        self.check_outputs(changer_start_accept_expected=[()],
               fsm_reset_sell_expected=[()],
               changer_stop_accept_expected=[(), ()],
               changer_dispense_amount_expected=[((PRODUCTS[product]-1,),)],
               fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_3_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of bills on a lower amount
        4) Wait accept timeout
        5) Return coins on accepted amount
        6) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.2
        
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.check_bill_amount(PRODUCTS[product]-6)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()
        
        self.check_bill_amount(5)
        
        #4
        yield self.sleep_defer(sleep_sec=0.5)
        
        #5
        self.check_outputs(validator_start_accept_expected=[()],
                   validator_stack_bill_expected=[()],
                   fsm_reset_sell_expected=[()],
                   changer_stop_accept_expected=[()],
                   changer_dispense_amount_expected=[((PRODUCTS[product]-1,),)],
                   fsm_ready_expected=[()])
        

    @defer.inlineCallbacks
    def test_scenarious_3_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of coins and bills on a lower amount
        4) Wait accept timeout
        5) Return coins on accepted amount
        6) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.2
        
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-6)
        self.reset_outputs()

        self.check_bill_amount(5)
        
        #4
        yield self.sleep_defer(sleep_sec=0.5)
        
        #5
        self.check_outputs(validator_start_accept_expected=[()],
                   validator_stack_bill_expected=[()],
                   fsm_reset_sell_expected=[()],
                   changer_stop_accept_expected=[()],
                   changer_dispense_amount_expected=[((PRODUCTS[product]-1,),)],
                   fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_4_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of some coins
        4) Payment of bill on which is impossible return change
        5) Return bill
        6) Wait accept timeout
        7) Return coins on accepted amount
        8) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.2
        self.changer.can_dispense_amount = MagicMock(return_value=False)
        
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-9)
        self.accept_coin_amount(3)
        self.reset_outputs()

        #4
        self.check_bill_amount(6, accept_bill=False)
        yield self.sleep_defer(sleep_sec=0.1)
        
        #5
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_start_accept_expected=[()])
       
        #6
        yield self.sleep_defer(sleep_sec=0.5)
        
        #7, 8
        self.check_outputs(fsm_reset_sell_expected=[()],
                   changer_stop_accept_expected=[()],
                   changer_dispense_amount_expected=[((PRODUCTS[product]-6,),)],
                   fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_4_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of some bills
        4) Payment of bill on which is impossible return change
        5) Return bill
        6) Wait accept timeout
        7) Return coins on accepted amount
        8) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.4
        
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.check_bill_amount(PRODUCTS[product]-9)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_bill_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()

        #4
        self.changer.can_dispense_amount = MagicMock(return_value=False)
        self.check_bill_amount(6, accept_bill=False)
        yield self.sleep_defer(sleep_sec=0.1)
        
        #5
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_start_accept_expected=[()])
        
        #6
        yield self.sleep_defer(sleep_sec=0.5)
        
        #7, 8
        self.check_outputs(fsm_reset_sell_expected=[()],
                   changer_stop_accept_expected=[()],
                   changer_dispense_amount_expected=[((PRODUCTS[product]-6,),)],
                   fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_4_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of some coins and bills
        4) Payment of bill on which is impossible return change
        5) Return bill
        6) Wait accept timeout
        7) Return coins on accepted amount
        8) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.4
        
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-9)
        self.check_bill_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()

        #4
        self.changer.can_dispense_amount = MagicMock(return_value=False)
        self.check_bill_amount(6, accept_bill=False)
        yield self.sleep_defer(sleep_sec=0.1)
        
        #5
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_start_accept_expected=[()])
        
        #6
        yield self.sleep_defer(sleep_sec=0.5)
        
        #7, 8
        self.check_outputs(fsm_reset_sell_expected=[()],
                   changer_stop_accept_expected=[()],
                   changer_dispense_amount_expected=[((PRODUCTS[product]-6,),)],
                   fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_4_4(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of bill on which is impossible return change
        4) Return bill
        5) Wait accept timeout
        6) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.2
        self.changer.can_dispense_amount = MagicMock(return_value=False)
        
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.check_bill_amount(PRODUCTS[product], accept_bill=False)
        yield self.sleep_defer(sleep_sec=0.1)
        
        #4
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_start_accept_expected=[()])
       
        #5
        yield self.sleep_defer(sleep_sec=0.5)
        
        #6
        self.check_outputs(fsm_reset_sell_expected=[()],
                           changer_stop_accept_expected=[()],
                           fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_4_5(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment of bill on which is impossible return change
        4) Return bill
        5) Payment of coins and bills on enough amount
        6) Prepare product
        7) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.4
        self.changer.can_dispense_amount = MagicMock(return_value=False)
        
        #1        
        self.set_kiosk_ready_state()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.check_bill_amount(PRODUCTS[product], accept_bill=False)
        yield self.sleep_defer(sleep_sec=0.1)
        
        #4
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_start_accept_expected=[()])

        #5
        self.changer.can_dispense_amount = MagicMock(return_value=True)
        self.accept_coin_amount(PRODUCTS[product]-1)
        self.check_bill_amount(1)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           plc_prepare_expected=[((PRODUCT_1,),)],
                           validator_stack_bill_expected=[()])

        #6
        self.product_prepared()
        
        #7
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_5_1(self):
        '''
        1) Wait select product
        2) Get Error Coin Jam from changer
        3) Go to error state
        4) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        self.fire_changer_error(error_code=changer.ERROR_CODE_COIN_JAM, 
                                error_text='error')
        
        #3
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_COIN_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #4
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_5_2(self):
        '''
        1) Wait select product
        2) Get Error Defective Tube Sensor from changer
        3) Go to error state
        4) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                            error_text='error')
        
        #3
        self.check_outputs(fsm_error_expected=[
                       ({'error_code':changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                         'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #4
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_5_3(self):
        '''
        1) Wait select product
        2) Get Error ROM Checksum Error from changer
        3) Go to error state
        4) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                            error_text='error')
        
        #3
        self.check_outputs(
               fsm_error_expected=[
                           ({'error_code':changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                             'error_text':'error'},)],
               changer_stop_accept_expected=[()])
        
        #4
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_5_4(self):
        '''
        1) Wait select product
        2) Get Error Tube Jam from changer
        3) Go to error state
        4) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        self.fire_changer_error(error_code=changer.ERROR_CODE_TUBE_JAM, 
                                error_text='error')
        
        #3
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_TUBE_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #4
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_6_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Get Error Coin Jam from changer
        4) Go to error state
        5) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.fire_changer_error(error_code=changer.ERROR_CODE_COIN_JAM, 
                                error_text='error')
        
        #4
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_COIN_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #5
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_6_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Get Error Defective Tube Sensor from changer
        4) Go to error state
        5) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                            error_text='error')
        
        #4
        self.check_outputs(fsm_error_expected=[
                       ({'error_code':changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                         'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #5
        yield self.check_kiosk_is_not_serviced()
        

    @defer.inlineCallbacks
    def test_scenarious_6_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Get Error ROM Checksum Error from changer
        4) Go to error state
        5) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                            error_text='error')
        
        #4
        self.check_outputs(fsm_error_expected=[
                           ({'error_code':changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                             'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #5
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_6_4(self):
        '''
        1) Wait select product
        2) Select product
        3) Get Error Tube Jam from changer
        4) Go to error state
        5) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.fire_changer_error(error_code=changer.ERROR_CODE_TUBE_JAM, 
                                error_text='error')
        
        #4
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_TUBE_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #5
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_7_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Start payment
        4) Get Error Coin Jam from changer
        5) Return accepted amount
        6) Go to error state
        7) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(2)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()

        #4
        self.fire_changer_error(error_code=changer.ERROR_CODE_COIN_JAM, 
                                error_text='error')
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #5, 6
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_COIN_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()],
                           changer_dispense_amount_expected=[((PRODUCTS[product]-1,),)])
        
        #7
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_7_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Start payment
        4) Get Error Tube Jam from changer
        5) Return accepted amount
        6) Go to error state
        7) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(2)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()

        #4
        self.fire_changer_error(error_code=changer.ERROR_CODE_TUBE_JAM, 
                                error_text='error')
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #5, 6
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_TUBE_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()],
                           changer_dispense_amount_expected=[((PRODUCTS[product]-1,),)])
        
        #7
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_8_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Start payment
        4) Get Error Defective Tube Sensor from changer
        5) Return accepted amount
        6) Go to error state
        7) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(2)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()

        #4
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                            error_text='error')
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #5, 6
        self.check_outputs(fsm_error_expected=[
                       ({'error_code':changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                         'error_text':'error'},)],
                           changer_stop_accept_expected=[()],
                           changer_dispense_amount_expected=[((PRODUCTS[product]-1,),)])
        
        #7
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_8_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Start payment
        4) Get Error ROM Checksum Error from changer
        5) Return accepted amount
        6) Go to error state
        7) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(2)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()

        #4
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                            error_text='error')
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #5, 6
        self.check_outputs(fsm_error_expected=[
                           ({'error_code':changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                             'error_text':'error'},)],
                   changer_stop_accept_expected=[()],
                   changer_dispense_amount_expected=[((PRODUCTS[product]-1,),)])
        
        #7
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_9_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on enough amount
        4) Get Error Coin Jam from changer
        5) Prepare product 
        6) Go to error state
        7) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.fire_changer_error(error_code=changer.ERROR_CODE_COIN_JAM, 
                                error_text='error')

        #5
        self.product_prepared()
        
        #6
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_COIN_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #7
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_9_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on enough amount
        4) Get Error Defective Tube Sensor from changer
        5) Prepare product 
        6) Go to error state
        7) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                            error_text='error')

        #5
        self.product_prepared()
        
        #6
        self.check_outputs(fsm_error_expected=[
                       ({'error_code':changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                         'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #7
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_9_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on enough amount
        4) Get Error ROM Checksum Error from changer
        5) Prepare product 
        6) Go to error state
        7) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                            error_text='error')

        #5
        self.product_prepared()
        
        #6
        self.check_outputs(fsm_error_expected=[
                           ({'error_code':changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                             'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #7
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_9_4(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on enough amount
        4) Get Error Tube Jam from changer
        5) Prepare product 
        6) Go to error state
        7) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.fire_changer_error(error_code=changer.ERROR_CODE_TUBE_JAM, 
                                error_text='error')

        #5
        self.product_prepared()
        
        #6
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_TUBE_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()])
        
        #7
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_10_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Get Error Defective Tube Sensor from changer
        5) Prepare product 
        6) Return change
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                            error_text='error')

        #5
        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #6, 7
        self.check_outputs(fsm_error_expected=[
                       ({'error_code':changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                         'error_text':'error'},)],
                           changer_stop_accept_expected=[()],
                           changer_dispense_amount_expected=[((1,),)])
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_10_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Get Error ROM Checksum Error from changer
        5) Prepare product 
        6) Return change
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                            error_text='error')

        #5
        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #6, 7
        self.check_outputs(fsm_error_expected=[
                           ({'error_code':changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                             'error_text':'error'},)],
                           changer_stop_accept_expected=[()],
                           changer_dispense_amount_expected=[((1,),)])
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_11_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Get Error Coin Jam from changer
        5) Prepare product 
        6) Return change
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.fire_changer_error(error_code=changer.ERROR_CODE_COIN_JAM, 
                                error_text='error')

        #5
        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #6, 7
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_COIN_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()],
                           changer_dispense_amount_expected=[((1,),)])
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_11_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Get Error Tube Jam from changer
        5) Prepare product 
        6) Return change
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.fire_changer_error(error_code=changer.ERROR_CODE_TUBE_JAM, 
                                error_text='error')

        #5
        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #6, 7
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_TUBE_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()],
                           changer_dispense_amount_expected=[((1,),)])
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_12_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error Coin Jam from changer during change depensing
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_changer_error(error_code=changer.ERROR_CODE_COIN_JAM, 
                                error_text='error')
        self.fire_coin_out(1)

        #7
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_COIN_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()],)
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_12_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error Defective Tube Sensor from changer during change depensing
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                            error_text='error')
        self.fire_coin_out(1)

        #7
        self.check_outputs(fsm_error_expected=[
                       ({'error_code':changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                         'error_text':'error'},)],
                           changer_stop_accept_expected=[()],)
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_12_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error ROM Checksum Error from changer during change depensing
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                            error_text='error')
        self.fire_coin_out(1)

        #7
        self.check_outputs(fsm_error_expected=[
                           ({'error_code':changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                             'error_text':'error'},)],
                           changer_stop_accept_expected=[()],)
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_12_4(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error Tube Jam from changer during change depensing
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_changer_error(error_code=changer.ERROR_CODE_TUBE_JAM, 
                                error_text='error')
        self.fire_coin_out(1)

        #7
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_TUBE_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()],)
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_13_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error Coin Jam from changer after change depensed
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_coin_out(1)
        self.check_outputs(fsm_ready_expected=[()])
        
        self.fire_changer_error(error_code=changer.ERROR_CODE_COIN_JAM, 
                                error_text='error')

        #7
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_COIN_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()],)
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_13_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error Defective Tube Sensor from changer after change depensed
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_coin_out(1)
        self.check_outputs(fsm_ready_expected=[()])
        
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                            error_text='error')

        #7
        self.check_outputs(fsm_error_expected=[
                       ({'error_code':changer.ERROR_CODE_DEFECTIVE_TUBE_SENSOR, 
                         'error_text':'error'},)],
                           changer_stop_accept_expected=[()],)
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_13_3(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error ROM Checksum Error from changer after change depensed
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_coin_out(1)
        self.check_outputs(fsm_ready_expected=[()])
        
        self.fire_changer_error(
                            error_code=changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                            error_text='error')

        #7
        self.check_outputs(fsm_error_expected=[
                           ({'error_code':changer.ERROR_CODE_ROM_CHECKSUM_ERROR, 
                             'error_text':'error'},)],
                           changer_stop_accept_expected=[()],)
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_13_4(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error Tube Jam from changer after change depensed
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(plc_prepare_expected=[((PRODUCT_1,),)],
                           changer_start_accept_expected=[()],
                           changer_stop_accept_expected=[(), ()],
                           validator_stack_bill_expected=[()])
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_coin_out(1)
        self.check_outputs(fsm_ready_expected=[()])
        
        self.fire_changer_error(error_code=changer.ERROR_CODE_TUBE_JAM, 
                                error_text='error')

        #7
        self.check_outputs(fsm_error_expected=[
                                   ({'error_code':changer.ERROR_CODE_TUBE_JAM, 
                                     'error_text':'error'},)],
                           changer_stop_accept_expected=[()],)
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_14(self):
        '''
        1) Wait select product
        2) Get Error from validator
        3) Go to error state
        4) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        self.fire_validator_error(error_code=1, error_text='error')
        
        #3
        self.check_outputs(fsm_error_expected=[({'error_code':1, 
                                                 'error_text':'error'},)],
                           validator_return_bill_expected=[()],
                           validator_stop_accept_expected=[()])
        
        #4
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_15_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Get Error from validator
        4) Go to error state
        5) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.fire_validator_error(error_code=1, error_text='error')
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #4
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_stop_accept_expected=[()],
                           changer_stop_accept_expected=[()],
                           fsm_error_expected=[({'error_code':1, 
                                                 'error_text':'error'},)])

        #5
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_15_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Start payment
        4) Get Error from validator
        5) Return accepted amount
        6) Go to error state
        7) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_outputs(changer_stop_accept_expected=[()],
                           changer_start_accept_expected=[()])
        
        #4
        self.fire_validator_error(error_code=1, error_text='error')
        
        yield self.sleep_defer(sleep_sec=0.1)
        
        #5, 6
        self.check_outputs(validator_return_bill_expected=[()],
                   validator_stop_accept_expected=[()],
                   changer_stop_accept_expected=[()],
                   changer_dispense_amount_expected=[((PRODUCTS[product]-3,),)],
                   fsm_error_expected=[({'error_code':1, 
                                         'error_text':'error'},)])
        
        #7
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_16(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on enough amount
        4) Get Error from validator
        5) Prepare product
        6) Return change
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()
        
        #4
        self.fire_validator_error(error_code=1, error_text='error')
        
        #5
        self.product_prepared()
        
        #6, 7
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_stop_accept_expected=[()],
                           changer_dispense_amount_expected=[((1,),)],
                           fsm_error_expected=[({'error_code':1, 
                                                 'error_text':'error'},)])

        self.fire_coin_out(1)
        self.check_outputs()
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_17(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error from validator during change depensing
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.reset_outputs()
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_validator_error(error_code=1, error_text='error')
        self.fire_coin_out(1)

        #7
        self.check_outputs(fsm_error_expected=[({'error_code':1, 
                                                 'error_text':'error'},)],
                           validator_return_bill_expected=[()],
                           validator_stop_accept_expected=[()])
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_18(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product 
        5) Return change
        6) Get Error from validator after change depensed
        7) Go to error state
        8) Check kiosk is not serviced
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(4)
        yield self.sleep_defer(sleep_sec=0.1)

        self.reset_outputs()
        
        #4
        self.product_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #6
        self.fire_coin_out(1)
        self.check_outputs(fsm_ready_expected=[()])
        
        self.fire_validator_error(error_code=1, error_text='error')
        yield self.sleep_defer(sleep_sec=0.1)

        #7
        self.check_outputs(fsm_error_expected=[({'error_code':1, 
                                                 'error_text':'error'},)],
                           validator_return_bill_expected=[()],
                           validator_stop_accept_expected=[()])
        
        #8
        yield self.check_kiosk_is_not_serviced()


    @defer.inlineCallbacks
    def test_scenarious_19(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Product prepare error 
        5) Return accepted amount
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #3
        self.accept_coin_amount(PRODUCTS[product]-3)
        self.check_bill_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()
        
        #4
        self.product_not_prepared()

        #5
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(
                   changer_dispense_amount_expected=[((PRODUCTS[product],),)])

        #6
        self.fire_coin_out(PRODUCTS[product])
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_20(self):
        '''
        1) Wait select product
        2) Lost connection with changer 
        3) Select product
        4) Wait coin accept timeout
        5) Reset product preparement
        6) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.2
        
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        self.set_changer_offline()

        #3
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()
        
        #check bill not accepted
        self.check_bill_amount(PRODUCTS[product], accept_bill=False)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_start_accept_expected=[()])
        
        #4
        yield self.sleep_defer(sleep_sec=0.2)

        #5, 6
        self.check_outputs(fsm_reset_sell_expected=[()],
                           fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_21(self):
        '''
        1) Wait select product
        2) Select product
        3) Lost connection with changer 
        4) Wait coin accept timeout
        5) Reset product preparement
        6) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.2
        
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.set_changer_offline()
        
        #check bill not accepted
        self.check_bill_amount(PRODUCTS[product], accept_bill=False)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_start_accept_expected=[()])
        
        #4
        yield self.sleep_defer(sleep_sec=0.2)

        #5, 6
        self.check_outputs(fsm_reset_sell_expected=[()],
                           fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_22(self):
        '''
        1) Wait select product
        2) Select product
        3) Start payment
        4) Lost connection with changer 
        5) Wait coin accept timeout
        6) Reset product preparement
        7) Go to ready state
        '''
        self.cash_fsm.accept_timeout_sec = 0.4
        
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.check_bill_amount(PRODUCTS[product]-2)
        self.accept_coin_amount(1)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()

        #4
        self.set_changer_offline()
        
        #check bill not accepted
        self.check_bill_amount(PRODUCTS[product], accept_bill=False)
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(validator_return_bill_expected=[()],
                           validator_start_accept_expected=[()])
        
        #5
        yield self.sleep_defer(sleep_sec=0.4)

        #6, 7
        self.check_outputs(fsm_reset_sell_expected=[()],
                           fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_23(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on enough amount
        4) Lost connection with changer 
        5) Prepare product
        6) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.check_bill_amount(PRODUCTS[product]-2)
        yield self.sleep_defer(sleep_sec=0.1)
        self.accept_coin_amount(2)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(changer_stop_accept_expected=[()],
                           validator_stack_bill_expected=[()],
                           validator_start_accept_expected=[()],
                           plc_prepare_expected=[((PRODUCT_1,),)])
        
        #4
        self.set_changer_offline()

        #5
        self.product_prepared()
        
        #6
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_24_1(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Lost connection with changer 
        5) Prepare product
        6) Appearance connection with changer
        7) Dispense change
        8) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.check_bill_amount(PRODUCTS[product]-2)
        yield self.sleep_defer(sleep_sec=0.1)
        self.accept_coin_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(changer_stop_accept_expected=[()],
                           validator_stack_bill_expected=[()],
                           validator_start_accept_expected=[()],
                           plc_prepare_expected=[((PRODUCT_1,),)])
        
        #4
        self.set_changer_offline()
        
        #5 - product prepare in process
        
        #6
        self.set_changer_online()

        #product prepared
        self.product_prepared()
        
        #7
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])
        
        self.fire_coin_out(1)

        #8
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_24_2(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Lost connection with changer 
        5) Prepare product
        6) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()
        
        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.check_bill_amount(PRODUCTS[product]-2)
        yield self.sleep_defer(sleep_sec=0.1)
        self.accept_coin_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(changer_stop_accept_expected=[()],
                           validator_stack_bill_expected=[()],
                           validator_start_accept_expected=[()],
                           plc_prepare_expected=[((PRODUCT_1,),)])
        
        #4
        self.set_changer_offline()
        
        #5
        self.product_prepared()
        
        #6
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_25(self):
        '''
        1) Wait select product
        2) Lost connection with validator 
        3) Select product
        4) Payment on more amount
        5) Prepare product
        6) Dispense change
        7) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        self.set_validator_offline()
        
        #3
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #4
        self.accept_coin_amount(PRODUCTS[product]-2)
        self.accept_coin_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(changer_stop_accept_expected=[(), ()],
                           changer_start_accept_expected=[()],
                           plc_prepare_expected=[((PRODUCT_1,),)])
        
        #5
        self.product_prepared()

        #6        
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])
        
        self.fire_coin_out(1)

        #7
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_26(self):
        '''
        1) Wait select product
        2) Select product
        3) Lost connection with validator 
        4) Payment on more amount
        5) Prepare product
        6) Dispense change
        7) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.set_validator_offline()

        #4
        self.accept_coin_amount(PRODUCTS[product]-2)
        self.accept_coin_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)

        self.check_outputs(changer_stop_accept_expected=[(), ()],
                           changer_start_accept_expected=[()],
                           plc_prepare_expected=[((PRODUCT_1,),)])
        
        #5
        self.product_prepared()

        #6        
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])
        
        self.fire_coin_out(1)

        #7
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_27(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Lost connection with validator 
        5) Prepare product
        6) Dispense change
        7) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.check_bill_amount(PRODUCTS[product]-2)
        self.accept_coin_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()

        #4
        self.set_validator_offline()
        
        #5
        self.product_prepared()

        #6        
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])
        
        self.fire_coin_out(1)

        #7
        self.check_outputs(fsm_ready_expected=[()])


    @defer.inlineCallbacks
    def test_scenarious_28(self):
        '''
        1) Wait select product
        2) Select product
        3) Payment on more amount
        4) Prepare product
        5) Lost connection with validator 
        6) Dispense change
        7) Go to ready state
        '''
        #1        
        self.set_kiosk_ready_state()
        self.reset_outputs()

        #2
        product=PRODUCT_1
        self.kiosk_fsm.sell(product=product)
        self.reset_outputs()

        #3
        self.check_bill_amount(PRODUCTS[product]-2)
        self.accept_coin_amount(3)
        yield self.sleep_defer(sleep_sec=0.1)
        self.reset_outputs()

        #4
        self.product_prepared()
        
        yield self.sleep_defer(sleep_sec=0.1)
        self.check_outputs(changer_dispense_amount_expected=[((1,),)])

        #5
        self.set_validator_offline()

        #6        
        self.fire_coin_out(1)

        #7
        self.check_outputs(fsm_ready_expected=[()])

        
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


    def fire_coin_out(self, amount):
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=amount)


    def fire_changer_error(self, error_code=1, error_text='error_1'):
        dispatcher.send_minimal(
            sender=self.changer, 
            signal='error', error_code=error_code, error_text=error_text)


    def fire_validator_error(self, error_code=1, error_text='error_1'):
        dispatcher.send_minimal(
            sender=self.validator, 
            signal='error', error_code=error_code, error_text=error_text)


    def check_bill_amount(self, amount, accept_bill=True):
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=amount)
        if accept_bill:
            dispatcher.send_minimal(
                sender=self.validator, signal='bill_in', amount=amount)

    def product_prepared(self):
        dispatcher.send_minimal(
            sender=self.plc, signal='prepared')


    def product_not_prepared(self):
        dispatcher.send_minimal(
            sender=self.plc, signal='not_prepared')


    def set_changer_offline(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        self.changer.can_dispense_amount = MagicMock(return_value=False)


    def set_validator_offline(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')


    def set_changer_online(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        self.changer.can_dispense_amount = MagicMock(return_value=True)


    def check_kiosk_is_not_serviced(self):
        self.kiosk_fsm.sell(product=PRODUCT_1)
        self.check_outputs()
        
        self.check_bill_amount(1)
        
        def callback_func(dont_care):
            self.check_outputs(validator_return_bill_expected=[()])
            
        return task.deferLater(reactor, 0.1, callback_func, None)
        
        
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
                      fsm_ready_expected=[],
                      fsm_reset_sell_expected=[],
                      fsm_error_expected=[],
                      changer_start_accept_expected=[],
                      changer_stop_accept_expected=[],
                      changer_dispense_amount_expected=[],
                      validator_start_accept_expected=[],
                      validator_stop_accept_expected=[],
                      validator_stack_bill_expected=[],
                      validator_return_bill_expected=[],
                      plc_prepare_expected=[]):
        
        self.assertEquals(fsm_ready_expected, 
                          self.fsm_listener.ready.call_args_list)
        self.assertEquals(fsm_reset_sell_expected, 
                          self.fsm_listener.reset_sell.call_args_list)
        self.assertEquals(fsm_error_expected, 
                          self.fsm_listener.error.call_args_list)
        self.assertEquals(changer_start_accept_expected, 
                          self.changer.start_accept.call_args_list)
        self.assertEquals(changer_stop_accept_expected, 
                          self.changer.stop_accept.call_args_list)
        self.assertEquals(changer_dispense_amount_expected, 
                          self.changer.dispense_amount.call_args_list)
        self.assertEquals(validator_start_accept_expected, 
                          self.validator.start_accept.call_args_list)
        self.assertEquals(validator_stop_accept_expected, 
                          self.validator.stop_accept.call_args_list)
        self.assertEquals(validator_stack_bill_expected, 
                          self.validator.stack_bill.call_args_list)
        self.assertEquals(validator_return_bill_expected, 
                          self.validator.return_bill.call_args_list)
        self.assertEquals(plc_prepare_expected, 
                          self.plc.prepare.call_args_list)
        
        self.reset_outputs()


    def sleep_defer(self, sleep_sec):
        return task.deferLater(reactor, sleep_sec, defer.passthru, None)
