
from louie import dispatcher

from twisted.internet import reactor, defer, task

# from unittest import TestCase
from twisted.trial import unittest

from kiosk.fsm.validator_fsm import BillValidatorFSM

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock
    

class TestValidatorFsm(unittest.TestCase):
    
    def setUp(self):
        self.fsm_listener = MagicMock()
        self.fsm_listener.online = MagicMock(spec="online")
        self.fsm_listener.offline = MagicMock(spec="offline")
        self.fsm_listener.initialized = MagicMock(spec="initialized")
        self.fsm_listener.error = MagicMock(spec="error")
        self.fsm_listener.bill_in = MagicMock(spec="bill_in")
        self.fsm_listener.check_bill = MagicMock(spec="check_bill")
        
        self.validator = MagicMock()
        self.validator.start_accept = MagicMock()
        self.validator.stop_accept = MagicMock()
        self.validator.stack_bill = MagicMock()
        self.validator.return_bill = MagicMock()
        
        self.validator_fsm = BillValidatorFSM(validator=self.validator)
        
        dispatcher.connect(self.fsm_listener.online, 
                           sender=self.validator_fsm, signal='online')
        dispatcher.connect(self.fsm_listener.offline, 
                           sender=self.validator_fsm, signal='offline')
        dispatcher.connect(self.fsm_listener.initialized, 
                           sender=self.validator_fsm, signal='initialized')
        dispatcher.connect(self.fsm_listener.error, 
                           sender=self.validator_fsm, signal='error')
        dispatcher.connect(self.fsm_listener.bill_in, 
                           sender=self.validator_fsm, signal='bill_in')
        dispatcher.connect(self.fsm_listener.check_bill, 
                           sender=self.validator_fsm, signal='check_bill')


    def tearDown(self):
        pass


    #                           1    2    3    4    5    6    7    8    9    10    
    # inputs
    # fsm.state("OFF",         OFF  OFF  OFF  OFF  OFF  OFF  OFF  OFF  OFF  OFF
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WB",
    #          "BC")                
    # validator.online               +
    # validator.offline                   +
    # validator.error                          +
    # validator.initialized                         +
    # validator.check_bill                               +
    # start_accept                                            +
    # stop_accept                                                  +
    # ban_bill                                                          +
    # permit_bill                                                            +
    #
    # outputs
    # fsm_listener.online       -    +    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    -    -    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -    -
    # fsm_listener.bill_in      -    -    -    -    -    -    -    -    -    -
    # fsm_listener.check_bill   -    -    -    -    -    -    -    -    -    -
    # validator.start_accept    -    -    -    -    -    -    -    -    -    -
    # validator.stop_accept     -    -    -    -    -    -    -    -    -    -
    # validator.stack_bill      -    -    -    -    -    -    -    -    -    -
    # validator.return_bill     -    -    -    -    -    -    -    -    -    -



    def test_1_on_offline(self):
        self.check_outputs()


    def test_2_validator_online_on_offline(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs(fsm_online_expected=[()])


    def test_3_validator_offline_on_offline(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs()


    def test_4_validator_error_on_offline(self):
        dispatcher.send_minimal(
            sender=self.validator, 
            signal='error', error_code=12, error_text="error_12")

        self.check_outputs()


    def test_5_validator_initialized_on_offline(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')

        self.check_outputs()


    def test_6_check_bill_on_offline(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)

        self.check_outputs()


    def test_7_start_accept_on_offline(self):
        self.validator_fsm.start_accept()

        self.check_outputs()


    def test_8_stop_accept_on_offline(self):
        self.validator_fsm.stop_accept()

        self.check_outputs()


    def test_9_ban_bill_on_offline(self):
        self.validator_fsm.ban_bill()

        self.check_outputs()


    def test_10_permit_bill_on_offline(self):
        self.validator_fsm.permit_bill()

        self.check_outputs()


    #                          11   12   13   14   15   16   17   18   19    
    # inputs
    # fsm.state("OFF",         ON   ON   ON   ON   ON   ON   ON   ON   ON
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WB",
    #          "BC")                
    # validator.online          +
    # validator.offline              +
    # validator.error                     +
    # validator.initialized                    +
    # validator.check_bill                          +
    # start_accept                                       +
    # stop_accept                                             +
    # ban_bill                                                     +
    # permit_bill                                                       +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    +    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    +    -    -    -    -    -
    # fsm_listener.bill_in      -    -    -    -    -    -    -    -    -
    # fsm_listener.check_bill   -    -    -    -    -    -    -    -    -
    # validator.start_accept    -    -    -    +    -    -    -    -    -
    # validator.stop_accept     -    -    +    -    -    -    -    -    -
    # validator.stack_bill      -    -    -    -    -    -    -    -    -
    # validator.return_bill     -    -    +    -    -    -    -    -    -

    def test_11_validator_online_on_online(self):
        self.set_fsm_state_online()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_12_validator_offline_on_online(self):
        self.set_fsm_state_online()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected=[()])


    def test_13_validator_error_on_online(self):
        self.set_fsm_state_online()
        
        dispatcher.send_minimal(
            sender=self.validator, 
            signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected=[({'error_code':12, 
                                                 'error_text':'error_12'},)],
                           validator_stop_accept_expected=[()],
                           validator_return_bill_expected=[()])


    def test_14_validator_initialized_on_online(self):
        self.set_fsm_state_online()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        
        self.check_outputs(fsm_initialized_expected=[()],
                           validator_start_accept_expected=[()])


    def test_15_check_bill_on_online(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)

        self.check_outputs()


    def test_16_start_accept_on_online(self):
        self.validator_fsm.start_accept()

        self.check_outputs()


    def test_17_stop_accept_on_online(self):
        self.validator_fsm.stop_accept()

        self.check_outputs()


    def test_18_ban_bill_on_online(self):
        self.validator_fsm.ban_bill()

        self.check_outputs()


    def test_18_permit_bill_on_online(self):
        self.validator_fsm.permit_bill()

        self.check_outputs()


    #                          20   21   22   23   24   25   26   27   28    
    # inputs
    # fsm.state("OFF",         ERR  ERR  ERR  ERR  ERR  ERR  ERR  ERR  ERR
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WB",
    #          "BC")                
    # validator.online          +
    # validator.offline              +
    # validator.error                     +
    # validator.initialized                    +
    # validator.check_bill                          +
    # start_accept                                       +
    # stop_accept                                             +
    # ban_bill                                                     +
    # permit_bill                                                       +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    -    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -
    # fsm_listener.bill_in      -    -    -    -    -    -    -    -    -
    # fsm_listener.check_bill   -    -    -    -    -    -    -    -    -
    # validator.start_accept    -    -    -    -    -    -    -    -    -
    # validator.stop_accept     -    -    -    -    -    -    -    -    -
    # validator.stack_bill      -    -    -    -    -    -    -    -    -
    # validator.return_bill     -    -    -    -    -    -    -    -    -

    def test_20_validator_online_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_21_validator_offline_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected=[()])


    def test_22_validator_error_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator, 
            signal='error', error_code=12, error_text="error_12")

        self.check_outputs()


    def test_23_validator_initialized_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')

        self.check_outputs()


    def test_24_check_bill_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)

        self.check_outputs(validator_return_bill_expected=[()])


    def test_25_start_accept_on_error(self):
        self.set_fsm_state_error()
        
        self.validator_fsm.start_accept()

        self.check_outputs()


    def test_26_stop_accept_on_error(self):
        self.set_fsm_state_error()
        
        self.validator_fsm.stop_accept()

        self.check_outputs()


    def test_27_ban_bill_on_error(self):
        self.set_fsm_state_error()
        
        self.validator_fsm.ban_bill()

        self.check_outputs()


    def test_28_permit_bill_on_error(self):
        self.set_fsm_state_error()
        
        self.validator_fsm.permit_bill()

        self.check_outputs()


    #                          29   30   31   32   33   34   35   36   37    
    # inputs
    # fsm.state("OFF",         RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WB",
    #          "BC")                
    # validator.online          +
    # validator.offline              +
    # validator.error                     +
    # validator.initialized                    +
    # validator.check_bill                          +
    # start_accept                                       +
    # stop_accept                                             +
    # ban_bill                                                     +
    # permit_bill                                                       +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    +    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -
    # fsm_listener.bill_in      -    -    -    -    -    -    -    -    -
    # fsm_listener.check_bill   -    -    -    -    -    -    -    -    -
    # validator.start_accept    -    -    -    -    -    +    -    -    -
    # validator.stop_accept     -    -    +    -    -    -    -    -    -
    # validator.stack_bill      -    -    -    -    -    -    -    -    -
    # validator.return_bill     -    -    +    -    +    -    -    -    -


    def test_29_validator_online_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_30_validator_offline_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected=[()])


    def test_31_validator_error_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, 
            signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected=[({'error_code':12, 
                                                 'error_text':'error_12'},)],
                           validator_stop_accept_expected=[()],
                           validator_return_bill_expected=[()])


    def test_32_validator_initialized_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        
        self.check_outputs()


    def test_33_check_bill_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)
        
        self.check_outputs(validator_return_bill_expected=[()])


    def test_34_start_accept_on_ready(self):
        self.set_fsm_state_initialized()

        self.validator_fsm.start_accept()
        
        self.check_outputs(validator_start_accept_expected=[()])


    def test_35_stop_accept_on_ready(self):
        self.set_fsm_state_initialized()

        self.validator_fsm.stop_accept()

        self.check_outputs()


    def test_36_ban_bill_on_ready(self):
        self.set_fsm_state_initialized()

        self.validator_fsm.ban_bill()

        self.check_outputs()


    def test_37_permit_bill_on_ready(self):
        self.set_fsm_state_initialized()

        self.validator_fsm.permit_bill()

        self.check_outputs()


    #                          38   39   40   41   42   43   44   45   46    
    # inputs
    # fsm.state("OFF",         WB   WB   WB   WB   WB   WB   WB   WB   WB
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WB",
    #          "BC")                
    # validator.online          +
    # validator.offline              +
    # validator.error                     +
    # validator.initialized                    +
    # validator.check_bill                          +
    # start_accept                                       +
    # stop_accept                                             +
    # ban_bill                                                     +
    # permit_bill                                                       +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    +    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -
    # fsm_listener.bill_in      -    -    -    -    -    -    -    -    -
    # fsm_listener.check_bill   -    -    -    -    +    -    -    -    -
    # validator.start_accept    -    -    -    -    -    -    -    -    -
    # validator.stop_accept     -    -    +    -    -    -    -    -    -
    # validator.stack_bill      -    -    -    -    -    -    -    -    -
    # validator.return_bill     -    -    +    -    -    -    -    -    -


    def test_38_validator_online_on_wait_bill(self):
        self.set_fsm_state_wait_bill()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_39_validator_offline_on_wait_bill(self):
        self.set_fsm_state_wait_bill()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected=[()])


    def test_40_validator_error_on_wait_bill(self):
        self.set_fsm_state_wait_bill()

        dispatcher.send_minimal(
            sender=self.validator, 
            signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected=[({'error_code':12, 
                                                 'error_text':'error_12'},)],
                           validator_stop_accept_expected=[()],
                           validator_return_bill_expected=[()])


    def test_41_validator_initialized_on_wait_bill(self):
        self.set_fsm_state_wait_bill()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')

        self.check_outputs()


    def test_42_check_bill_on_wait_bill(self):
        self.set_fsm_state_wait_bill()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)

        self.check_outputs(fsm_check_bill_expected=[({'amount':1,},)])


    def test_43_start_accept_on_wait_bill(self):
        self.set_fsm_state_wait_bill()
        
        self.validator_fsm.start_accept()

        self.check_outputs()


    def test_44_stop_accept_on_wait_bill(self):
        self.set_fsm_state_wait_bill()
        
        self.validator_fsm.stop_accept()

        self.check_outputs()


    def test_45_ban_bill_on_wait_bill(self):
        self.set_fsm_state_wait_bill()
        
        self.validator_fsm.ban_bill()

        self.check_outputs()


    def test_46_permit_bill_on_wait_bill(self):
        self.set_fsm_state_wait_bill()
        
        self.validator_fsm.permit_bill()

        self.check_outputs()


    #                          47   48   49   50   51   52   53   54   55    
    # inputs
    # fsm.state("OFF",         BC   BC   BC   BC   BC   BC   BC   BC   BC
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WB",
    #          "BC")                
    # validator.online          +
    # validator.offline              +
    # validator.error                     +
    # validator.initialized                    +
    # validator.check_bill                          +
    # start_accept                                       +
    # stop_accept                                             +
    # ban_bill                                                     +
    # permit_bill                                                       +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    +    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -
    # fsm_listener.bill_in      -    -    -    -    -    -    -    -    +
    # fsm_listener.check_bill   -    -    -    -    -    -    -    -    -
    # validator.start_accept    -    -    -    -    -    -    -    -    -
    # validator.stop_accept     -    -    +    -    -    -    -    -    -
    # validator.stack_bill      -    -    -    -    -    -    -    -    +
    # validator.return_bill     -    -    +    -    -    -    -    +    -


    def test_47_validator_online_on_bill_confirm(self):
        self.set_fsm_state_bill_confirm()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_48_validator_offline_on_bill_confirm(self):
        self.set_fsm_state_bill_confirm()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected=[()])


    def test_49_validator_error_on_bill_confirm(self):
        self.set_fsm_state_bill_confirm()

        dispatcher.send_minimal(
            sender=self.validator, 
            signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected=[({'error_code':12, 
                                                 'error_text':'error_12'},)],
                           validator_stop_accept_expected=[()],
                           validator_return_bill_expected=[()])


    def test_50_validator_initialized_on_bill_confirm(self):
        self.set_fsm_state_bill_confirm()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')

        self.check_outputs()


    def test_51_check_bill_on_bill_confirm(self):
        self.set_fsm_state_bill_confirm()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)

        self.check_outputs()


    def test_52_start_accept_on_bill_confirm(self):
        self.set_fsm_state_bill_confirm()
        
        self.validator_fsm.start_accept()

        self.check_outputs()


    def test_53_stop_accept_on_bill_confirm(self):
        self.set_fsm_state_bill_confirm()
        
        self.validator_fsm.stop_accept()

        self.check_outputs()


    def test_54_ban_bill_on_bill_confirm(self):
        self.set_fsm_state_bill_confirm()
        
        self.validator_fsm.ban_bill()

        self.check_outputs(validator_return_bill_expected=[()])



    @defer.inlineCallbacks
    def test_55_permit_bill_on_bill_confirm(self):
        self.set_fsm_state_bill_confirm(amount=10)
        
        self.validator_fsm.permit_bill()
        
        yield self.sleep_defer(sleep_sec=0.5)

        self.check_outputs(validator_stack_bill_expected=[()])
        self.validator.stack_bill.reset_mock()

        dispatcher.send_minimal(
            sender=self.validator, signal='bill_in', amount=10)

        self.check_outputs(fsm_bill_in_expected=[({'amount':10,},)])


    def set_fsm_state_online(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='online')
        self.fsm_listener.online.reset_mock()
        
        
    def set_fsm_state_error(self):
        self.set_fsm_state_online()
        dispatcher.send_minimal(
            sender=self.validator, 
            signal='error', error_code='12', error_text='error_12')
        self.fsm_listener.error.reset_mock()
        self.validator.stop_accept.reset_mock()
        self.validator.return_bill.reset_mock()
        
        
    def set_fsm_state_initialized(self):
        self.set_fsm_state_online()
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        self.fsm_listener.initialized.reset_mock()
        self.validator.start_accept.reset_mock()


    def set_fsm_state_wait_bill(self):
        self.set_fsm_state_initialized()
        self.validator_fsm.start_accept()
        self.validator.start_accept.reset_mock()


    def set_fsm_state_bill_confirm(self, amount=10):
        self.set_fsm_state_wait_bill()
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=amount)
        self.fsm_listener.check_bill.reset_mock()


    def check_outputs(self,
                      fsm_online_expected=[],
                      fsm_offline_expected=[],
                      fsm_error_expected=[],
                      fsm_initialized_expected=[],
                      fsm_bill_in_expected=[],
                      fsm_check_bill_expected=[],
                      validator_start_accept_expected=[],
                      validator_stop_accept_expected=[],
                      validator_stack_bill_expected=[],
                      validator_return_bill_expected=[]):
        self.assertEquals(fsm_online_expected, 
                          self.fsm_listener.online.call_args_list)
        self.assertEquals(fsm_offline_expected, 
                          self.fsm_listener.offline.call_args_list)
        self.assertEquals(fsm_error_expected, 
                          self.fsm_listener.error.call_args_list)
        self.assertEquals(fsm_initialized_expected, 
                          self.fsm_listener.initialized.call_args_list)
        self.assertEquals(fsm_bill_in_expected, 
                          self.fsm_listener.bill_in.call_args_list)
        self.assertEquals(fsm_check_bill_expected, 
                          self.fsm_listener.check_bill.call_args_list)
        self.assertEquals(validator_start_accept_expected, 
                          self.validator.start_accept.call_args_list)
        self.assertEquals(validator_stop_accept_expected, 
                          self.validator.stop_accept.call_args_list)
        self.assertEquals(validator_stack_bill_expected, 
                          self.validator.stack_bill.call_args_list)
        self.assertEquals(validator_return_bill_expected, 
                          self.validator.return_bill.call_args_list)


    def sleep_defer(self, sleep_sec):
        return task.deferLater(reactor, sleep_sec, defer.passthru, None)
