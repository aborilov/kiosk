
from louie import dispatcher

from unittest import TestCase

from kiosk.fsm.validator_fsm import BillValidatorFSM

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock
    

class TestValidatorFsm(TestCase):
    
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
        
        dispatcher.connect(self.fsm_listener.online, sender=self.validator_fsm, signal='online')
        dispatcher.connect(self.fsm_listener.offline, sender=self.validator_fsm, signal='offline')
        dispatcher.connect(self.fsm_listener.initialized, sender=self.validator_fsm, signal='initialized')
        dispatcher.connect(self.fsm_listener.error, sender=self.validator_fsm, signal='error')
        dispatcher.connect(self.fsm_listener.bill_in, sender=self.validator_fsm, signal='bill_in')
        dispatcher.connect(self.fsm_listener.check_bill, sender=self.validator_fsm, signal='check_bill')


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



    def test_1(self):
        self.check_outputs()


    def test_2(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs(fsm_online_expected_args_list=[()])


    def test_3_10(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')
        dispatcher.send_minimal(
            sender=self.validator, signal='error', error_code=12, error_text="error_12")
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)
        self.validator_fsm.start_accept()
        self.validator_fsm.stop_accept()
        self.validator_fsm.ban_bill()
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
    # validator.return_bill     -    -    -    -    -    -    -    -    -

    def test_11(self):
        self.set_fsm_state_online()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_12(self):
        self.set_fsm_state_online()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_13(self):
        self.set_fsm_state_online()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           validator_stop_accept_expected_args_list=[()])


    def test_14(self):
        self.set_fsm_state_online()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        
        self.check_outputs(fsm_initialized_expected_args_list=[()],
                           validator_start_accept_expected_args_list=[()])


    def test_15_19(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)
        self.validator_fsm.start_accept()
        self.validator_fsm.stop_accept()
        self.validator_fsm.ban_bill()
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

    def test_20(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_21(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_22_28(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='error', error_code=12, error_text="error_12")
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)
        self.validator_fsm.start_accept()
        self.validator_fsm.stop_accept()
        self.validator_fsm.ban_bill()
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
    # validator.return_bill     -    -    -    -    +    -    -    -    -


    def test_29(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_30(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_31(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           validator_stop_accept_expected_args_list=[()])


    def test_32(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        
        self.check_outputs()


    def test_33(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)
        
        self.check_outputs(validator_return_bill_expected_args_list=[()])


    def test_34(self):
        self.set_fsm_state_initialized()

        self.validator_fsm.start_accept()
        
        self.check_outputs(validator_start_accept_expected_args_list=[()])


    def test_35_37(self):
        self.set_fsm_state_initialized()

        self.validator_fsm.stop_accept()
        self.validator_fsm.ban_bill()
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
    # validator.return_bill     -    -    -    -    -    -    -    -    -


    def test_38(self):
        self.set_fsm_state_wait_bill()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_39(self):
        self.set_fsm_state_wait_bill()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_40(self):
        self.set_fsm_state_wait_bill()

        dispatcher.send_minimal(
            sender=self.validator, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           validator_stop_accept_expected_args_list=[()])


    def test_41(self):
        self.set_fsm_state_wait_bill()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')

        self.check_outputs()


    def test_42(self):
        self.set_fsm_state_wait_bill()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)

        self.check_outputs(fsm_check_bill_expected_args_list=[({'amount':1,},)])


    def test_43_46(self):
        self.set_fsm_state_wait_bill()
        
        self.validator_fsm.start_accept()
        self.validator_fsm.stop_accept()
        self.validator_fsm.ban_bill()
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
    # validator.return_bill     -    -    -    -    -    -    -    +    -


    def test_47(self):
        self.set_fsm_state_bill_confirm()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='online')

        self.check_outputs()


    def test_48(self):
        self.set_fsm_state_bill_confirm()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='offline')

        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_49(self):
        self.set_fsm_state_bill_confirm()

        dispatcher.send_minimal(
            sender=self.validator, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           validator_stop_accept_expected_args_list=[()])


    def test_50_53(self):
        self.set_fsm_state_bill_confirm()
        
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=1)
        self.validator_fsm.start_accept()
        self.validator_fsm.stop_accept()

        self.check_outputs()


    def test_54(self):
        self.set_fsm_state_bill_confirm()
        
        self.validator_fsm.ban_bill()

        self.check_outputs(validator_return_bill_expected_args_list=[()])


    def test_55(self):
        self.set_fsm_state_bill_confirm(amount=10)
        
        self.validator_fsm.permit_bill()

        self.check_outputs(fsm_bill_in_expected_args_list=[({'amount':10,},)],
                           validator_stack_bill_expected_args_list=[()])


    def set_fsm_state_online(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='online')
        self.fsm_listener.online.reset_mock()
        
        
    def set_fsm_state_error(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='online')
        self.fsm_listener.online.reset_mock()
        dispatcher.send_minimal(
            sender=self.validator, signal='error', error_code='12', error_text='error_12')
        self.fsm_listener.error.reset_mock()
        self.validator.stop_accept.reset_mock()
        
        
    def set_fsm_state_initialized(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='online')
        self.fsm_listener.online.reset_mock()
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        self.fsm_listener.initialized.reset_mock()
        self.validator.start_accept.reset_mock()


    def set_fsm_state_wait_bill(self):
        dispatcher.send_minimal(
            sender=self.validator, signal='online')
        self.fsm_listener.online.reset_mock()
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        self.fsm_listener.initialized.reset_mock()
        self.validator_fsm.start_accept()
        self.validator.start_accept.reset_mock()


    def set_fsm_state_bill_confirm(self, amount=10):
        dispatcher.send_minimal(
            sender=self.validator, signal='online')
        self.fsm_listener.online.reset_mock()
        dispatcher.send_minimal(
            sender=self.validator, signal='initialized')
        self.fsm_listener.initialized.reset_mock()
        self.validator_fsm.start_accept()
        self.validator.start_accept.reset_mock()
        dispatcher.send_minimal(
            sender=self.validator, signal='check_bill', amount=amount)
        self.fsm_listener.check_bill.reset_mock()


    def check_outputs(self,
                      fsm_online_expected_args_list=[],
                      fsm_offline_expected_args_list=[],
                      fsm_error_expected_args_list=[],
                      fsm_initialized_expected_args_list=[],
                      fsm_bill_in_expected_args_list=[],
                      fsm_check_bill_expected_args_list=[],
                      validator_start_accept_expected_args_list=[],
                      validator_stop_accept_expected_args_list=[],
                      validator_stack_bill_expected_args_list=[],
                      validator_return_bill_expected_args_list=[]):
        self.assertEquals(fsm_online_expected_args_list, self.fsm_listener.online.call_args_list)
        self.assertEquals(fsm_offline_expected_args_list, self.fsm_listener.offline.call_args_list)
        self.assertEquals(fsm_error_expected_args_list, self.fsm_listener.error.call_args_list)
        self.assertEquals(fsm_initialized_expected_args_list, self.fsm_listener.initialized.call_args_list)
        self.assertEquals(fsm_bill_in_expected_args_list, self.fsm_listener.bill_in.call_args_list)
        self.assertEquals(fsm_check_bill_expected_args_list, self.fsm_listener.check_bill.call_args_list)
        self.assertEquals(validator_start_accept_expected_args_list, self.validator.start_accept.call_args_list)
        self.assertEquals(validator_stop_accept_expected_args_list, self.validator.stop_accept.call_args_list)
        self.assertEquals(validator_stack_bill_expected_args_list, self.validator.stack_bill.call_args_list)
        self.assertEquals(validator_return_bill_expected_args_list, self.validator.return_bill.call_args_list)
