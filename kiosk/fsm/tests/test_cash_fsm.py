from louie import dispatcher

from twisted.internet import reactor, defer, task

#from unittest import TestCase
from twisted.trial import unittest

from kiosk.fsm.cash_fsm import CashFSM

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock
    

class TestCashFsm(unittest.TestCase):
    

    def setUp(self):
        self.fsm_listener = MagicMock()
        self.fsm_listener.ready = MagicMock(spec="ready")
        self.fsm_listener.accepted = MagicMock(spec="accepted")
        self.fsm_listener.not_accepted = MagicMock(spec="not_accepted")
        self.fsm_listener.dispensed = MagicMock(spec="dispensed")
        self.fsm_listener.error = MagicMock(spec="error")
        
        self.changer_fsm = MagicMock()
        self.changer_fsm.start = MagicMock()
        self.changer_fsm.start_accept = MagicMock()
        self.changer_fsm.stop_accept = MagicMock()
        self.changer_fsm.start_dispense = MagicMock()
        self.changer_fsm.stop_dispense = MagicMock()
        self.changer_fsm.can_dispense_amount = MagicMock(return_value=True)
        
        self.validator_fsm = MagicMock()
        self.validator_fsm.start = MagicMock()
        self.validator_fsm.start_accept = MagicMock()
        self.validator_fsm.stop_accept = MagicMock()
        self.validator_fsm.ban_bill = MagicMock()
        self.validator_fsm.permit_bill = MagicMock()
        
        self.cash_fsm = CashFSM(changer_fsm=self.changer_fsm, validator_fsm=self.validator_fsm)
        
        dispatcher.connect(self.fsm_listener.ready, sender=self.cash_fsm, signal='ready')
        dispatcher.connect(self.fsm_listener.accepted, sender=self.cash_fsm, signal='accepted')
        dispatcher.connect(self.fsm_listener.not_accepted, sender=self.cash_fsm, signal='not_accepted')
        dispatcher.connect(self.fsm_listener.error, sender=self.cash_fsm, signal='error')
        dispatcher.connect(self.fsm_listener.dispensed, sender=self.cash_fsm, signal='dispensed')


    def tearDown(self):
        pass


    #                             1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17
    # inputs
    # fsm.state("INI",           INI  INI  INI  INI  INI  INI  INI  INI  INI  INI  INI  INI  INI  INI  INI  INI  INI
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # start                            +
    # changer_fsm.online                    +
    # changer_fsm.offline                        +
    # changer_fsm.error                               +
    # changer_fsm.initialized                              +
    # changer_fsm.coin_in                                       +
    # changer_fsm.amount_dispensed                                   +
    # validator_fsm.online                                                +
    # validator_fsm.offline                                                    +
    # validator_fsm.error                                                           +
    # validator_fsm.initialized                                                          +
    # validator_fsm.bill_in                                                                   +
    # validator_fsm.check_bill                                                                     + 
    # accept                                                                                            +
    # dispense_change                                                                                        +
    # dispense_all                                                                                                +
    #
    # outputs
    # fsm_listener.ready          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.accepted       -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.not_accepted   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start           -    +    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_accept    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_accept     -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_dispense  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_dispense   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start         -    +    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start_accept  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.stop_accept   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.ban_bill      -    -    -    -    -    -    -    -    -    -    -    -    -    +    -    -    -
    # validator_fsm.permit_bill   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -


    def test_1_init(self):
        self.check_outputs()


    def test_2_cash_start_on_init(self):
        self.cash_fsm.start()

        self.check_outputs(changer_fsm_start_expected_args_list=[()],
                           validator_fsm_start_expected_args_list=[()])


    def test_3_changer_online_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')

        self.check_outputs()


    def test_4_changer_offline_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')

        self.check_outputs()


    def test_5_changer_error_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs()


    def test_6_changer_initialized_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')

        self.check_outputs()


    def test_7_coin_in_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=10)

        self.check_outputs()


    def test_8_amount_dispensed_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='amount_dispensed', amount=10)

        self.check_outputs()

    def test_9_validator_online_on_init(self):
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')

        self.check_outputs()


    def test_10_validator_offline_on_init(self):
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')

        self.check_outputs()


    def test_11_validator_error_on_init(self):
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs()


    def test_12_validator_initialized_on_init(self):
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')

        self.check_outputs()


    def test_13_bill_in_on_init(self):
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=10)

        self.check_outputs()


    def test_14_check_bill_on_init(self):
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='check_bill', amount=10)
        
        self.check_outputs(validator_fsm_ban_bill_expected_args_list=[((10,),)])


    def test_15_cash_accept_on_init(self):
        self.cash_fsm.accept(amount=10)
        
        self.check_outputs()


    def test_16_cash_dispense_change_on_init(self):
        self.cash_fsm.dispense_change()
        
        self.check_outputs()


    def test_17_cash_dispense_all_on_init(self):
        self.cash_fsm.dispense_all()
        
        self.check_outputs()


    #                            18   19   20   21
    # inputs
    # fsm.state("INI",           INI  INI  INI  INI
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # start (after setting             +    +    +
    #        device states)
    # changer_fsm.online                         +
    # changer_fsm.initialized     +    +    +
    # validator_fsm.online                  +
    # validator_fsm.initialized   +    +         +
    #
    # outputs
    # fsm_listener.ready          -    +    -    -
    # fsm_listener.accepted       -    -    -    -
    # fsm_listener.not_accepted   -    -    -    -
    # fsm_listener.dispensed      -    -    -    -
    # fsm_listener.error          -    -    -    -
    # changer_fsm.start           -    +    +    +
    # changer_fsm.start_accept    -    -    -    -
    # changer_fsm.stop_accept     -    -    -    -
    # changer_fsm.start_dispense  -    -    -    -
    # changer_fsm.stop_dispense   -    -    -    -
    # validator_fsm.start         -    +    +    +
    # validator_fsm.start_accept  -    -    -    -
    # validator_fsm.stop_accept   -    -    -    -
    # validator_fsm.ban_bill      -    -    -    -
    # validator_fsm.permit_bill   -    -    -    -

    def test_18_devices_initialized_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
        
        self.check_outputs()


    def test_19_devices_initialized_before_start_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
        
        self.cash_fsm.start()
        
        self.check_outputs(changer_fsm_start_expected_args_list=[()],
                           validator_fsm_start_expected_args_list=[()],
                           fsm_ready_expected_args_list=[()])


    def test_20_changer_initialized_validator_online_before_start_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')
        
        self.cash_fsm.start()
        
        self.check_outputs(changer_fsm_start_expected_args_list=[()],
                           validator_fsm_start_expected_args_list=[()])


    def test_21_changer_online_validator_initialized_before_start_on_init(self):
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
        
        self.cash_fsm.start()
        
        self.check_outputs(changer_fsm_start_expected_args_list=[()],
                           validator_fsm_start_expected_args_list=[()])


    #                            22   23   24   25   26   27   28   29   30   31   32   33   34   35   36   37
    # inputs
    # fsm.state("INI",           WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # start                       +
    # changer_fsm.online               +
    # changer_fsm.offline                   +
    # changer_fsm.error                          +
    # changer_fsm.initialized                         +
    # changer_fsm.coin_in                                  +
    # changer_fsm.amount_dispensed                              +
    # validator_fsm.online                                           +
    # validator_fsm.offline                                               +
    # validator_fsm.error                                                      +
    # validator_fsm.initialized                                                     +
    # validator_fsm.bill_in                                                              +
    # validator_fsm.check_bill                                                                +
    # accept                                                                                       +
    # dispense_change                                                                                   +
    # dispense_all                                                                                           +
    #
    # outputs
    # fsm_listener.ready          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.accepted       -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.not_accepted   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start           -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_accept    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_accept     -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_dispense  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_dispense   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start         -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start_accept  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.stop_accept   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.ban_bill      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.permit_bill   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -


    def test_22_cash_start_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        self.cash_fsm.start()

        self.check_outputs()


    def test_23_changer_online_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')

        self.check_outputs()


    def test_24_changer_offline_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')

        self.check_outputs()


    def test_25_changer_error_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs()


    def test_26_changer_initialized_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')

        self.check_outputs()


    def test_27_coin_in_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=10)

        self.check_outputs()


    def test_28_amount_dispensed_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='amount_dispensed', amount=10)

        self.check_outputs()

    def test_29_validator_online_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')

        self.check_outputs()


    def test_30_validator_offline_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')

        self.check_outputs()


    def test_31_validator_error_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs()


    def test_32_validator_initialized_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')

        self.check_outputs()


    def test_33_bill_in_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=10)

        self.check_outputs()


    def test_34_check_bill_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='check_bill', amount=10)
        
        self.check_outputs(validator_fsm_ban_bill_expected_args_list=[((10,),)])


    def test_35_cash_accept_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        self.cash_fsm.accept(amount=10)
        
        self.check_outputs()


    def test_36_cash_dispense_change_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        self.cash_fsm.dispense_change()
        
        self.check_outputs()


    def test_37_cash_dispense_all_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        self.cash_fsm.dispense_all()
        
        self.check_outputs()


    #                            38   39   40   41   42   43   44   45   46   47   48   49   50   51   52   53
    # inputs
    # fsm.state("INI",           WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR   WR
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # changer_fsm.online          +    +    +    +
    # changer_fsm.offline                             +    +    +    +
    # changer_fsm.error                                                   +    +    +    +
    # changer_fsm.initialized                                                                 +    +    +    +
    # validator_fsm.online        +                   +                   +                   +
    # validator_fsm.offline            +                   +                   +                   +
    # validator_fsm.error                   +                   +                   +                   +
    # validator_fsm.initialized                  +                   +                   +                   +
    #
    # outputs
    # fsm_listener.ready          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    +
    # fsm_listener.accepted       -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.not_accepted   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start           -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_accept    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_accept     -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_dispense  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_dispense   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start         -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start_accept  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.stop_accept   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.ban_bill      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.permit_bill   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -


    def test_38_devices_online_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')
        
        self.check_outputs()


    def test_39_changer_online_validator_offline_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')
        
        self.check_outputs()


    def test_40_changer_online_validator_error_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs()


    def test_41_changer_online_validator_initialized_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
        
        self.check_outputs()


    def test_42_changer_offline_validator_online_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')
        
        self.check_outputs()


    def test_43_devices_offline_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')
        
        self.check_outputs()


    def test_44_changer_offline_validator_error_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs()


    def test_45_changer_offline_validator_initialized_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
        
        self.check_outputs()


    def test_46_changer_error_validator_online_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')
        
        self.check_outputs()


    def test_47_changer_error_validator_offline_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')
        
        self.check_outputs()


    def test_48_devices_error_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=11, error_text='error_11')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs()


    def test_49_changer_error_validator_initialized_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
        
        self.check_outputs()


    def test_50_changer_initialized_validator_online_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')
        
        self.check_outputs()


    def test_51_changer_initialized_validator_offline_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')
        
        self.check_outputs()


    def test_52_changer_initialized_validator_error_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs()


    def test_53_devices_initialized_on_wait_ready(self):
        self.set_fsm_state_wait_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
        
        self.check_outputs(fsm_ready_expected_args_list=[()])


    #                            54   55   56   57   58   59   60   61   62   63   64   65   66   67   68   69
    # inputs
    # fsm.state("INI",           ERR  ERR  ERR  ERR  ERR  ERR  ERR  ERR  ERR  ERr  ERR  ERR  ERR  ERR  ERR  ERR
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # start                       +
    # changer_fsm.online               +
    # changer_fsm.offline                   +
    # changer_fsm.error                          +
    # changer_fsm.initialized                         +
    # changer_fsm.coin_in                                  +
    # changer_fsm.amount_dispensed                              +
    # validator_fsm.online                                           +
    # validator_fsm.offline                                               +
    # validator_fsm.error                                                      +
    # validator_fsm.initialized                                                     +
    # validator_fsm.bill_in                                                              +
    # validator_fsm.check_bill                                                                + 
    # accept                                                                                       +
    # dispense_change                                                                                   +
    # dispense_all                                                                                           +
    #
    # outputs
    # fsm_listener.ready          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.accepted       -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.not_accepted   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start           -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_accept    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_accept     -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_dispense  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_dispense   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start         -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start_accept  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.stop_accept   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.ban_bill      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.permit_bill   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -

    def test_54_cash_start_on_error(self):
        self.set_fsm_state_error()
        
        self.cash_fsm.start()

        self.check_outputs()


    def test_55_changer_online_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')

        self.check_outputs()


    def test_56_changer_offline_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')

        self.check_outputs()


    def test_57_changer_error_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs()


    def test_58_changer_initialized_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')

        self.check_outputs()


    def test_59_coin_in_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=10)

        self.check_outputs()


    def test_60_amount_dispensed_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='amount_dispensed', amount=10)

        self.check_outputs()

    def test_61_validator_online_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')

        self.check_outputs()


    def test_62_validator_offline_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')

        self.check_outputs()


    def test_63_validator_error_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs()


    def test_64_validator_initialized_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')

        self.check_outputs()


    def test_65_bill_in_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=10)

        self.check_outputs()


    def test_66_check_bill_on_error(self):
        self.set_fsm_state_error()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='check_bill', amount=10)
        
        self.check_outputs(validator_fsm_ban_bill_expected_args_list=[((10,),)])


    def test_67_cash_accept_on_error(self):
        self.set_fsm_state_error()
        
        self.cash_fsm.accept(amount=10)
        
        self.check_outputs()


    def test_68_cash_dispense_change_on_error(self):
        self.set_fsm_state_error()
        
        self.cash_fsm.dispense_change()
        
        self.check_outputs()


    def test_69_cash_dispense_all_on_error(self):
        self.set_fsm_state_error()
        
        self.cash_fsm.dispense_all()
        
        self.check_outputs()


    #                            70   71   72   73   74   75   76   77   78   79   80   81   82   83   84   85
    # inputs
    # fsm.state("INI",           RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # start                       +
    # changer_fsm.online               +
    # changer_fsm.offline                   +
    # changer_fsm.error                          +
    # changer_fsm.initialized                         +
    # changer_fsm.coin_in                                  +
    # changer_fsm.amount_dispensed                              +
    # validator_fsm.online                                           +
    # validator_fsm.offline                                               +
    # validator_fsm.error                                                      +
    # validator_fsm.initialized                                                     +
    # validator_fsm.bill_in                                                              +
    # validator_fsm.check_bill                                                                + 
    # accept                                                                                       +
    # dispense_change                                                                                   +
    # dispense_all                                                                                           +
    #
    # outputs
    # fsm_listener.ready          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.accepted       -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.not_accepted   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error          -    -    -    +    -    -    -    -    -    +    -    -    -    -    -    -
    # changer_fsm.start           -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_accept    -    -    -    -    -    -    -    -    -    -    -    -    -    +    -    -
    # changer_fsm.stop_accept     -    -    -    +    -    -    -    -    -    +    -    -    -    -    -    -
    # changer_fsm.start_dispense  -    -    -    -    -    +    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_dispense   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start         -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start_accept  -    -    -    -    -    -    -    -    -    -    -    -    -    +    -    -
    # validator_fsm.stop_accept   -    -    -    +    -    -    -    -    -    +    -    -    -    -    -    -
    # validator_fsm.ban_bill      -    -    -    -    -    -    -    -    -    -    -    -    +    -    -    -
    # validator_fsm.permit_bill   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -

    def test_70_cash_start_on_ready(self):
        self.set_fsm_state_ready()
        
        self.cash_fsm.start()

        self.check_outputs()


    def test_71_changer_online_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')

        self.check_outputs()


    def test_72_changer_offline_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')

        self.check_outputs()


    def test_73_changer_error_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_74_changer_initialized_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')

        self.check_outputs()


    def test_75_coin_in_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=10)

        self.check_outputs(changer_fsm_start_dispense_expected_args_list=[((10,),)])


    def test_76_amount_dispensed_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='amount_dispensed', amount=10)

        self.check_outputs()
        

    def test_77_validator_online_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')

        self.check_outputs()


    def test_78_validator_offline_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')

        self.check_outputs()


    def test_79_validator_error_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_80_validator_initialized_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')

        self.check_outputs()


    def test_81_bill_in_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=10)
        

        self.check_outputs()


    def test_82_check_bill_on_ready(self):
        self.set_fsm_state_ready()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='check_bill', amount=10)
        
        self.check_outputs(validator_fsm_ban_bill_expected_args_list=[((10,),)])


    def test_83_cash_accept_on_ready(self):
        self.set_fsm_state_ready()
        
        self.cash_fsm.accept(amount=10)
        
        self.check_outputs(changer_fsm_start_accept_expected_args_list=[()],
                           validator_fsm_start_accept_expected_args_list=[()])


    def test_84_cash_dispense_change_on_ready(self):
        self.set_fsm_state_ready()
        
        self.cash_fsm.dispense_change()
        
        self.check_outputs()


    def test_85_cash_dispense_all_on_ready(self):
        self.set_fsm_state_ready()
        
        self.cash_fsm.dispense_all()
        
        self.check_outputs()


    #                            86   87   88   89   90   91   92   93   94   95   96   97   98
    # inputs
    # fsm.state("INI",           AA   AA   AA   AA   AA   AA   AA   AA   AA   AA   AA   AA   AA
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # start                       +
    # changer_fsm.online               +
    # changer_fsm.offline                   +
    # changer_fsm.error                          +
    # changer_fsm.initialized                         +
    # changer_fsm.amount_dispensed                         +
    # validator_fsm.online                                      +
    # validator_fsm.offline                                          +
    # validator_fsm.error                                                 +
    # validator_fsm.initialized                                                +
    # accept                                                                        +
    # dispense_change                                                                    +
    # dispense_all                                                                            +
    #
    # outputs
    # fsm_listener.ready          -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.accepted       -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.not_accepted   -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed      -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error          -    -    -    +    -    -    -    -    +    -    -    -    -
    # changer_fsm.start           -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_accept    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_accept     -    -    -    +    -    -    -    -    +    -    -    -    -
    # changer_fsm.start_dispense  -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_dispense   -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start         -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start_accept  -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.stop_accept   -    -    -    +    -    -    -    -    +    -    -    -    -
    # validator_fsm.ban_bill      -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.permit_bill   -    -    -    -    -    -    -    -    -    -    -    -    -

    def test_86_cash_start_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        self.cash_fsm.start()

        self.check_outputs()


    def test_87_changer_online_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')

        self.check_outputs()


    def test_88_changer_offline_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')

        self.check_outputs()


    def test_89_changer_error_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_90_changer_initialized_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')

        self.check_outputs()


    def test_91_amount_dispensed_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='amount_dispensed', amount=10)

        self.check_outputs()
        

    def test_92_validator_online_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')

        self.check_outputs()


    def test_93_validator_offline_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')

        self.check_outputs()


    def test_94_validator_error_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')

        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_95_validator_initialized_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')

        self.check_outputs()


    def test_96_cash_accept_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        self.cash_fsm.accept(amount=10)
        
        self.check_outputs()


    def test_97_cash_dispense_change_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        self.cash_fsm.dispense_change()
        
        self.check_outputs()


    def test_98_cash_dispense_all_on_accept_amount(self):
        self.set_fsm_state_accept_amount()
        
        self.cash_fsm.dispense_all()
        
        self.check_outputs()


    #                                            99   100  101  102  103  104  105  106  107  108  109  110  111  112
    # inputs
    # fsm.state("INI",                           AA   AA   AA   AA   AA   AA   AA   AA   AA   AA   AA   AA   AA   AA
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # changer_fsm.coin_in (accepted               +    +
    #    sum isn't enough)
    # changer_fsm.coin_in (accepted                         +    +    +    +
    #    sum is enough)
    # validator_fsm.bill_in (accepted                                           +    +
    #    sum isn't enough)
    # validator_fsm.bill_in (accepted                                                     +    +    +    +
    #    sum is enough)
    # validator_fsm.check_bill (can                                                                           +
    #    dispense change)
    # validator_fsm.check_bill (cann't                                                                             +
    #    dispense change)
    #
    # outputs
    # fsm_listener.ready                          -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.accepted                       -    -    +    +    +    +    -    -    +    +    +    +    -    -
    # fsm_listener.not_accepted                   -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed                      -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error                          -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start                           -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_accept                    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_accept                     -    -    +    +    +    +    -    -    +    +    +    +    -    -
    # changer_fsm.start_dispense                  -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_dispense                   -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start                         -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start_accept                  -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.stop_accept                   -    -    +    +    +    +    -    -    +    +    +    +    -    -
    # validator_fsm.ban_bill                      -    -    -    -    -    -    -    -    -    -    -    -    -    +
    # validator_fsm.permit_bill                   -    -    -    -    -    -    -    -    -    -    -    -    +    -


    def test_99_coin_in_on_accept_amount(self):
        '''
        handling signal 'coin_in' in FSM state 'accept_amount' when accepted sum isn't enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=1)
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=4)
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=4)

        self.check_outputs(changer_fsm_start_accept_expected_args_list=[(), (), ()])


    def test_100_coin_in_on_accept_amount(self):
        '''
        handling signal 'coin_in' in FSM state 'accept_amount' when accepted sum isn't enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=9)

        self.check_outputs(changer_fsm_start_accept_expected_args_list=[()])


    def test_101_coin_in_on_accept_amount(self):
        '''
        handling signal 'coin_in' in FSM state 'accept_amount' when accepted sum is enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=10)

        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':10,},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_102_coin_in_on_accept_amount(self):
        '''
        handling signal 'coin_in' in FSM state 'accept_amount' when accepted sum is enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=9)
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=1)

        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':10,},)],
                           changer_fsm_start_accept_expected_args_list=[()],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_103_coin_in_on_accept_amount(self):
        '''
        handling signal 'coin_in' in FSM state 'accept_amount' when accepted sum is enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=9)
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=2)

        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':11,},)],
                           changer_fsm_start_accept_expected_args_list=[()],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_104_coin_in_on_accept_amount(self):
        '''
        handling signal 'coin_in' in FSM state 'accept_amount' when accepted sum is enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=11)

        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':11,},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_105_bill_in_on_accept_amount(self):
        '''
        handling signal 'bill_in' in FSM state 'accept_amount' when accepted sum isn't enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=1)
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=4)
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=4)

        self.check_outputs(validator_fsm_start_accept_expected_args_list=[(), (), ()])


    def test_106_bill_in_on_accept_amount(self):
        '''
        handling signal 'bill_in' in FSM state 'accept_amount' when accepted sum isn't enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=9)

        self.check_outputs(validator_fsm_start_accept_expected_args_list=[()])


    def test_107_bill_in_on_accept_amount(self):
        '''
        handling signal 'bill_in' in FSM state 'accept_amount' when accepted sum is enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=10)

        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':10,},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_108_bill_in_on_accept_amount(self):
        '''
        handling signal 'bill_in' in FSM state 'accept_amount' when accepted sum is enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=9)
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=1)

        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':10,},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_start_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_109_bill_in_on_accept_amount(self):
        '''
        handling signal 'bill_in' in FSM state 'accept_amount' when accepted sum is enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=9)
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=2)

        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':11,},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_start_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_110_bill_in_on_accept_amount(self):
        '''
        handling signal 'bill_in' in FSM state 'accept_amount' when accepted sum is enough
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=11)

        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':11,},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])


    def test_111_check_bill_on_accept_amount(self):
        '''
        handling signal 'check_bill' in FSM state 'accept_amount' when dispense change is possible
        '''
        self.set_fsm_state_accept_amount(amount=10)
        
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='check_bill', amount=10)
        
        self.check_outputs(validator_fsm_permit_bill_expected_args_list=[((10,),)])


    def test_112_check_bill_on_accept_amount(self):
        '''
        handling signal 'check_bill' in FSM state 'accept_amount' when dispense change isn't possible
        '''
        self.set_fsm_state_accept_amount(amount=10)
        self.changer_fsm.can_dispense_amount.return_value = False

        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='check_bill', amount=10)
        
        self.check_outputs(validator_fsm_ban_bill_expected_args_list=[((10,),)])


    #                                            113  114  115  116  117
    # inputs
    # fsm.state("INI",                           AA   AA   AA   AA   AA
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # accept_timeout = 2 sec                      +
    #    (no any payment during timeout)
    # accept_timeout = 2 sec                           +
    #    (not enough payment during timeout)
    # accept_timeout = 4 sec                                +
    #    (no any payment during timeout)
    # accept_timeout = 4 sec                                     +
    #    (not enough payment during timeout)
    # accept_timeout = 2 sec                                          +
    #    (enough payment during timeout)
    #
    # outputs
    # fsm_listener.ready                          -    -    -    -    -
    # fsm_listener.accepted                       -    -    -    -    +
    # fsm_listener.not_accepted                   +    +    +    +    -
    # fsm_listener.dispensed                      -    -    -    -    -
    # fsm_listener.error                          -    -    -    -    -
    # changer_fsm.start                           -    -    -    -    -
    # changer_fsm.start_accept                    -    -    -    -    -
    # changer_fsm.stop_accept                     -    -    -    -    -
    # changer_fsm.start_dispense                  -    -    -    -    -
    # changer_fsm.stop_dispense                   -    -    -    -    -
    # validator_fsm.start                         -    -    -    -    -
    # validator_fsm.start_accept                  -    -    -    -    -
    # validator_fsm.stop_accept                   -    -    -    -    -
    # validator_fsm.ban_bill                      -    -    -    -    -
    # validator_fsm.permit_bill                   -    -    -    -    -

    
    @defer.inlineCallbacks
    def test_113_accept_timeout_2_sec_on_accept_amount(self):
        '''
        check accept timeout exceed in FSM state 'accept_amount' when no any payment during timeout
        '''
        self.set_fsm_state_accept_amount(amount=10, accept_timeout_sec=2)
        
        yield self.sleep_defer(sleep_sec=1)
         
        self.check_outputs()

        yield self.sleep_defer(sleep_sec=2)
        
        self.check_outputs(fsm_not_accepted_expected_args_list=[()],
            changer_fsm_stop_accept_expected_args_list=[()],
            validator_fsm_stop_accept_expected_args_list=[()])
        

    @defer.inlineCallbacks
    def test_114_accept_timeout_2_sec_on_accept_amount(self):
        '''
        check accept timeout exceed in FSM state 'accept_amount' when not enough payment maked during timeout
        '''
        self.set_fsm_state_accept_amount(amount=10, accept_timeout_sec=2)

        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=9)
        
        yield self.sleep_defer(sleep_sec=1)
        
        self.check_outputs(changer_fsm_start_accept_expected_args_list=[()])
        self.reset_outputs()
            
        yield self.sleep_defer(sleep_sec=2)

        self.check_outputs(fsm_not_accepted_expected_args_list=[()],
            changer_fsm_stop_accept_expected_args_list=[()],
            validator_fsm_stop_accept_expected_args_list=[()],
            changer_fsm_start_dispense_expected_args_list=[((9,),)])


    @defer.inlineCallbacks
    def test_115_accept_timeout_4_sec_on_accept_amount(self):
        '''
        check accept timeout exceed in FSM state 'accept_amount' when no any payment during timeout
        '''
        self.set_fsm_state_accept_amount(amount=10, accept_timeout_sec=4)
        
        yield self.sleep_defer(sleep_sec=3)
        
        self.check_outputs()
            
        yield self.sleep_defer(sleep_sec=2)

        self.check_outputs(fsm_not_accepted_expected_args_list=[()],
            changer_fsm_stop_accept_expected_args_list=[()],
            validator_fsm_stop_accept_expected_args_list=[()])

        
    @defer.inlineCallbacks
    def test_116_accept_timeout_4_sec_on_accept_amount(self):
        '''
        check accept timeout exceed in FSM state 'accept_amount' when not enough payment maked during timeout
        '''
        self.set_fsm_state_accept_amount(amount=10, accept_timeout_sec=4)

        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=9)
        
        yield self.sleep_defer(sleep_sec=3)
        
        self.check_outputs(changer_fsm_start_accept_expected_args_list=[()])
        self.reset_outputs()
            
        yield self.sleep_defer(sleep_sec=2)

        self.check_outputs(fsm_not_accepted_expected_args_list=[()],
            changer_fsm_stop_accept_expected_args_list=[()],
            validator_fsm_stop_accept_expected_args_list=[()],
            changer_fsm_start_dispense_expected_args_list=[((9,),)])

    
    @defer.inlineCallbacks
    def test_117_accept_timeout_2_sec_on_accept_amount(self):
        '''
        check accept timeout not exceed in FSM state 'accept_amount' when enough payment maked during timeout
        '''
        self.set_fsm_state_accept_amount(amount=10, accept_timeout_sec=2)

        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=10)

        yield self.sleep_defer(sleep_sec=3)
        
        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':10,},)],
            changer_fsm_stop_accept_expected_args_list=[()],
            validator_fsm_stop_accept_expected_args_list=[()])

        
 
    #                            118  119  120  121  122  123  124  125  126  127  128  129  130  131  132  133
    # inputs
    # fsm.state("INI",           WD   WD   WD   WD   WD   WD   WD   WD   WD   WD   WD   WD   WD   WD   WD   WD
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # start                       +
    # changer_fsm.online               +
    # changer_fsm.offline                   +
    # changer_fsm.error                          +
    # changer_fsm.initialized                         +
    # changer_fsm.coin_in                                  +
    # changer_fsm.amount_dispensed                              +
    # validator_fsm.online                                           +
    # validator_fsm.offline                                               +
    # validator_fsm.error                                                      +
    # validator_fsm.initialized                                                     +
    # validator_fsm.bill_in                                                              +
    # validator_fsm.check_bill                                                                + 
    # accept                                                                                       +
    # dispense_change                                                                                   +
    # dispense_all                                                                                           +
    #
    # outputs
    # fsm_listener.ready          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.accepted       -    -    -    -    -    +    -    -    -    -    -    +    -    -    -    -
    # fsm_listener.not_accepted   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error          -    -    -    +    -    -    -    -    -    +    -    -    -    -    -    -
    # changer_fsm.start           -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_accept    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_accept     -    -    -    +    -    -    -    -    -    +    -    -    -    -    -    -
    # changer_fsm.start_dispense  -    -    -    -    -    -    -    -    -    -    -    -    -    -    +    +
    # changer_fsm.stop_dispense   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start         -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start_accept  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.stop_accept   -    -    -    +    -    -    -    -    -    +    -    -    -    -    -    -
    # validator_fsm.ban_bill      -    -    -    -    -    -    -    -    -    -    -    -    +    -    -    -
    # validator_fsm.permit_bill   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
 
 
    def test_118_cash_start_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        self.cash_fsm.start()
 
        self.check_outputs()
 
 
    def test_119_changer_online_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')
 
        self.check_outputs()
 
 
    def test_120_changer_offline_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')
 
        self.check_outputs()
 
 
    def test_121_changer_error_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')
 
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])
 
 
    def test_122_changer_initialized_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
 
        self.check_outputs()
 
 
    def test_123_coin_in_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense(10)
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=1)
 
        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':11,},)])
 
 
    def test_124_amount_dispensed_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='amount_dispensed', amount=10)
 
        self.check_outputs()
         
 
    def test_125_validator_online_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')
 
        self.check_outputs()
 
 
    def test_126_validator_offline_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')
 
        self.check_outputs()
 
 
    def test_127_validator_error_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')
 
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])
 
 
    def test_128_validator_initialized_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
 
        self.check_outputs()
 
 
    def test_129_bill_in_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense(10)
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=1)
 
        self.check_outputs(fsm_accepted_expected_args_list=[({'amount':11,},)])
 
 
    def test_130_check_bill_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='check_bill', amount=10)
         
        self.check_outputs(validator_fsm_ban_bill_expected_args_list=[((10,),)])
 
 
    def test_131_cash_accept_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense()
         
        self.cash_fsm.accept(amount=10)
         
        self.check_outputs()
 
 
    def test_132_cash_dispense_change_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense(10)
        
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=1)
        
        self.fsm_listener.accepted.reset_mock()
        
        self.cash_fsm.dispense_change()
         
        self.check_outputs(changer_fsm_start_dispense_expected_args_list=[((1,),)])
 
 
    def test_133_cash_dispense_all_on_wait_dispense(self):
        self.set_fsm_state_wait_dispense(10)
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=1)

        self.fsm_listener.accepted.reset_mock()
        
        self.cash_fsm.dispense_all()
         
        self.check_outputs(changer_fsm_start_dispense_expected_args_list=[((11,),)])


    #                            134  135  136  137  138  139  140  141  142  143  144  145  146  147  148  149
    # inputs
    # fsm.state("INI",           SD   SD   SD   SD   SD   SD   SD   SD   SD   SD   SD   SD   SD   SD   SD   SD
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # start                       +
    # changer_fsm.online               +
    # changer_fsm.offline                   +
    # changer_fsm.error                          +
    # changer_fsm.initialized                         +
    # changer_fsm.coin_in                                  +
    # changer_fsm.amount_dispensed                              +
    # validator_fsm.online                                           +
    # validator_fsm.offline                                               +
    # validator_fsm.error                                                      +
    # validator_fsm.initialized                                                     +
    # validator_fsm.bill_in                                                              +
    # validator_fsm.check_bill                                                                + 
    # accept                                                                                       +
    # dispense_change                                                                                   +
    # dispense_all                                                                                           +
    #
    # outputs
    # fsm_listener.ready          -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.accepted       -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.not_accepted   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed      -    -    -    -    -    -    +    -    -    -    -    -    -    -    -    -
    # fsm_listener.error          -    -    -    +    -    -    -    -    -    +    -    -    -    -    -    -
    # changer_fsm.start           -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.start_accept    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_accept     -    -    -    +    -    -    -    -    -    +    -    -    -    -    -    -
    # changer_fsm.start_dispense  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer_fsm.stop_dispense   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start         -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.start_accept  -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # validator_fsm.stop_accept   -    -    -    +    -    -    -    -    -    +    -    -    -    -    -    -
    # validator_fsm.ban_bill      -    -    -    -    -    -    -    -    -    -    -    -    +    -    -    -
    # validator_fsm.permit_bill   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -


    def test_134_cash_start_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        self.cash_fsm.start()
 
        self.check_outputs()
 
 
    def test_135_changer_online_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='online')
 
        self.check_outputs()
 
 
    def test_136_changer_offline_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='offline')
 
        self.check_outputs()
 
 
    def test_137_changer_error_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code=12, error_text='error_12')
 
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])
 
 
    def test_138_changer_initialized_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
 
        self.check_outputs()
 
 
    def test_139_coin_in_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=1)
 
        self.check_outputs()
 
 
    def test_140_amount_dispensed_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='amount_dispensed', amount=10)
 
        self.check_outputs(fsm_dispensed_expected_args_list=[({'amount':10,},)])
         
 
    def test_141_validator_online_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='online')
 
        self.check_outputs()
 
 
    def test_142_validator_offline_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='offline')
 
        self.check_outputs()
 
 
    def test_143_validator_error_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='error', error_code=12, error_text='error_12')
 
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_fsm_stop_accept_expected_args_list=[()],
                           validator_fsm_stop_accept_expected_args_list=[()])
 
 
    def test_144_validator_initialized_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
 
        self.check_outputs()
 
 
    def test_145_bill_in_on_start_dispense(self):
        self.set_fsm_state_start_dispense(10)
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='bill_in', amount=1)
 
        self.check_outputs()
 
 
    def test_146_check_bill_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='check_bill', amount=10)
         
        self.check_outputs(validator_fsm_ban_bill_expected_args_list=[((10,),)])
 
 
    def test_147_cash_accept_on_start_dispense(self):
        self.set_fsm_state_start_dispense()
         
        self.cash_fsm.accept(amount=10)
         
        self.check_outputs()
 
 
    def test_148_cash_dispense_change_on_start_dispense(self):
        self.set_fsm_state_start_dispense(10)
        self.cash_fsm.dispense_change()
         
        self.check_outputs()
 
 
    def test_149_cash_dispense_all_on_start_dispense(self):
        self.set_fsm_state_start_dispense(10)
         
        self.cash_fsm.dispense_all()
         
        self.check_outputs()


    #                                            150
    # inputs
    # fsm.state("INI",                           AA
    #          "WR",
    #          "ERR",
    #          "RDY",
    #          "AA",
    #          "WD",                
    #          "SD")
    # accept_timeout = 4 sec                      +
    #    (not enough payment during timeout)
    #
    # outputs
    # fsm_listener.ready                          -
    # fsm_listener.accepted                       -
    # fsm_listener.not_accepted                   +
    # fsm_listener.dispensed                      -
    # fsm_listener.error                          -
    # changer_fsm.start                           -
    # changer_fsm.start_accept                    -
    # changer_fsm.stop_accept                     -
    # changer_fsm.start_dispense                  -
    # changer_fsm.stop_dispense                   -
    # validator_fsm.start                         -
    # validator_fsm.start_accept                  -
    # validator_fsm.stop_accept                   -
    # validator_fsm.ban_bill                      -
    # validator_fsm.permit_bill                   -

    @defer.inlineCallbacks
    def test_150_accept_timeout_4_sec_on_accept_amount(self):
        '''
        check accept timeout exceed in FSM state 'accept_amount' when not enough payment maked during timeout
        '''
        self.set_fsm_state_accept_amount(amount=10, accept_timeout_sec=4)

        yield self.sleep_defer(sleep_sec=3)

        self.check_outputs()

        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=9)
        
        yield self.sleep_defer(sleep_sec=3)
        
        self.check_outputs(changer_fsm_start_accept_expected_args_list=[()])
        self.reset_outputs()
            
        yield self.sleep_defer(sleep_sec=2)

        self.check_outputs(fsm_not_accepted_expected_args_list=[()],
            changer_fsm_stop_accept_expected_args_list=[()],
            validator_fsm_stop_accept_expected_args_list=[()],
            changer_fsm_start_dispense_expected_args_list=[((9,),)])


    def set_fsm_state_wait_ready(self):
        self.cash_fsm.start()
        self.changer_fsm.start.reset_mock()
        self.validator_fsm.start.reset_mock()
        
        
    def set_fsm_state_error(self):
        self.set_fsm_state_wait_ready()
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='error', error_code='12', error_text='error_12')
        self.fsm_listener.error.reset_mock()
        
        
    def set_fsm_state_ready(self, accept_timeout_sec=0):
        self.set_fsm_state_wait_ready()
        self.cash_fsm.accept_timeout_sec = accept_timeout_sec
        dispatcher.send_minimal(
            sender=self.validator_fsm, signal='initialized')
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='initialized')
        self.fsm_listener.ready.reset_mock()


    def set_fsm_state_accept_amount(self, amount=10, accept_timeout_sec=0):
        self.set_fsm_state_ready(accept_timeout_sec=accept_timeout_sec)
        self.cash_fsm.accept(amount=amount)
        self.validator_fsm.start_accept.reset_mock()
        self.changer_fsm.start_accept.reset_mock()


    def set_fsm_state_wait_dispense(self, amount=10):
        self.set_fsm_state_accept_amount(amount=amount)
        dispatcher.send_minimal(
            sender=self.changer_fsm, signal='coin_in', amount=amount)
        self.changer_fsm.stop_accept.reset_mock()
        self.validator_fsm.stop_accept.reset_mock()
        self.fsm_listener.accepted.reset_mock()


    def set_fsm_state_start_dispense(self, amount=10):
        self.set_fsm_state_wait_dispense(amount=amount)
        self.cash_fsm.dispense_all()
        self.changer_fsm.start_dispense.reset_mock()


    def check_outputs(self,
                      fsm_ready_expected_args_list=[],
                      fsm_accepted_expected_args_list=[],
                      fsm_not_accepted_expected_args_list=[],
                      fsm_dispensed_expected_args_list=[],
                      fsm_error_expected_args_list=[],
                      changer_fsm_start_expected_args_list=[],
                      changer_fsm_start_accept_expected_args_list=[],
                      changer_fsm_stop_accept_expected_args_list=[],
                      changer_fsm_start_dispense_expected_args_list=[],
                      changer_fsm_stop_dispense_expected_args_list=[],
                      validator_fsm_start_expected_args_list=[],
                      validator_fsm_start_accept_expected_args_list=[],
                      validator_fsm_stop_accept_expected_args_list=[],
                      validator_fsm_ban_bill_expected_args_list=[],
                      validator_fsm_permit_bill_expected_args_list=[]):
        self.assertEquals(fsm_ready_expected_args_list, self.fsm_listener.ready.call_args_list)
        self.assertEquals(fsm_accepted_expected_args_list, self.fsm_listener.accepted.call_args_list)
        self.assertEquals(fsm_not_accepted_expected_args_list, self.fsm_listener.not_accepted.call_args_list)
        self.assertEquals(fsm_dispensed_expected_args_list, self.fsm_listener.dispensed.call_args_list)
        self.assertEquals(fsm_error_expected_args_list, self.fsm_listener.error.call_args_list)
        self.assertEquals(changer_fsm_start_expected_args_list, self.changer_fsm.start.call_args_list)
        self.assertEquals(changer_fsm_start_accept_expected_args_list, self.changer_fsm.start_accept.call_args_list)
        self.assertEquals(changer_fsm_stop_accept_expected_args_list, self.changer_fsm.stop_accept.call_args_list)
        self.assertEquals(changer_fsm_start_dispense_expected_args_list, self.changer_fsm.start_dispense.call_args_list)
        self.assertEquals(changer_fsm_stop_dispense_expected_args_list, self.changer_fsm.stop_dispense.call_args_list)
        self.assertEquals(validator_fsm_start_expected_args_list, self.validator_fsm.start.call_args_list)
        self.assertEquals(validator_fsm_start_accept_expected_args_list, self.validator_fsm.start_accept.call_args_list)
        self.assertEquals(validator_fsm_stop_accept_expected_args_list, self.validator_fsm.stop_accept.call_args_list)
        self.assertEquals(validator_fsm_ban_bill_expected_args_list, self.validator_fsm.ban_bill.call_args_list)
        self.assertEquals(validator_fsm_permit_bill_expected_args_list, self.validator_fsm.permit_bill.call_args_list)


    def reset_outputs(self):
        self.fsm_listener.ready.reset_mock()
        self.fsm_listener.accepted.reset_mock()
        self.fsm_listener.not_accepted.reset_mock()
        self.fsm_listener.dispensed.reset_mock()
        self.fsm_listener.error.reset_mock()
        self.changer_fsm.start.reset_mock()
        self.changer_fsm.start_accept.reset_mock()
        self.changer_fsm.stop_accept.reset_mock()
        self.changer_fsm.start_dispense.reset_mock()
        self.changer_fsm.stop_dispense.reset_mock()
        self.validator_fsm.start.reset_mock()
        self.validator_fsm.start_accept.reset_mock()
        self.validator_fsm.stop_accept.reset_mock()
        self.validator_fsm.ban_bill.reset_mock()
        self.validator_fsm.permit_bill.reset_mock()


    def sleep_defer(self, sleep_sec):
        return task.deferLater(reactor, sleep_sec, defer.passthru, None)

