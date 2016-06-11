
from louie import dispatcher

from twisted.internet import reactor
from threading import Thread

import time

from unittest import TestCase

from kiosk.fsm.changer_fsm import ChangerFSM


try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock
    

class TestChangerFsm(TestCase):
    
    @classmethod
    def setUpClass(cls):
        Thread(target=reactor.run, args=(False,)).start()

    @classmethod
    def tearDownClass(cls):
        reactor.callFromThread(reactor.stop)

    def setUp(self):
        self.fsm_listener = MagicMock()
        self.fsm_listener.online = MagicMock(spec="online")
        self.fsm_listener.offline = MagicMock(spec="offline")
        self.fsm_listener.initialized = MagicMock(spec="initialized")
        self.fsm_listener.error = MagicMock(spec="error")
        self.fsm_listener.coin_in = MagicMock(spec="coin_in")
        self.fsm_listener.amount_dispensed = MagicMock(spec="amount_dispensed")
        
        self.changer = MagicMock()
        self.changer.start_accept = MagicMock()
        self.changer.stop_accept = MagicMock()
        self.changer.dispense_amount = MagicMock()
        
        self.changer_fsm = ChangerFSM(changer=self.changer)
        
        dispatcher.connect(self.fsm_listener.online, sender=self.changer_fsm, signal='online')
        dispatcher.connect(self.fsm_listener.offline, sender=self.changer_fsm, signal='offline')
        dispatcher.connect(self.fsm_listener.initialized, sender=self.changer_fsm, signal='initialized')
        dispatcher.connect(self.fsm_listener.error, sender=self.changer_fsm, signal='error')
        dispatcher.connect(self.fsm_listener.coin_in, sender=self.changer_fsm, signal='coin_in')
        dispatcher.connect(self.fsm_listener.amount_dispensed, sender=self.changer_fsm, signal='amount_dispensed')


    def tearDown(self):
        pass

    #                           1    2    3    4    5    6    7    8    9    10   11
    # inputs
    # fsm.state("OFF",         OFF  OFF  OFF  OFF  OFF  OFF  OFF  OFF  OFF  OFF  OFF
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WC",
    #          "DA")                
    # changer.online                 +
    # changer.offline                     +
    # changer.error                            +
    # changer.initialized                           +
    # changer.coin_in                                    +
    # changer.coin_out                                        +
    # start_accept                                                 +
    # stop_accept                                                       +
    # start_dispense                                                         +
    # stop_dispense                                                               +
    #
    # outputs
    # fsm_listener.online       -    +    -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -    -    -    
    # fsm_listener.coin_in      -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed    -    -    -    -    -    -    -    -    -    -    -
    # changer.start_accept      -    -    -    -    -    -    -    -    -    -    -
    # changer.stop_accept       -    -    -    -    -    -    -    -    -    -    -
    # changer.dispense_amount   -    -    -    -    -    -    -    -    -    -    -



    def test_1(self):
        self.check_outputs()

    def test_2(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')

        self.check_outputs(fsm_online_expected_args_list=[()])
        

    def test_3_11(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        dispatcher.send_minimal(
            sender=self.changer, signal='error', error_code=12, error_text="error_12")
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        self.changer_fsm.start_accept()
        self.changer_fsm.stop_accept()
        self.changer_fsm.start_dispense(amount=20)
        self.changer_fsm.stop_dispense()
        
        # delays until changer.dispense_amount executed
        time.sleep(1)

        self.check_outputs()


    #                          12   13   14   15   16   17   18   19   20   21
    # inputs
    # fsm.state("OFF",         ON   ON   ON   ON   ON   ON   ON   ON   ON   ON
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WC",
    #          "DA")                
    # changer.online            +
    # changer.offline                +
    # changer.error                       +
    # changer.initialized                      +
    # changer.coin_in                               +
    # changer.coin_out                                   +
    # start_accept                                            +
    # stop_accept                                                  +
    # start_dispense                                                    +
    # stop_dispense                                                          +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    +    -    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    +    -    -    -    -    -    -    
    # fsm_listener.coin_in      -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed    -    -    -    -    -    -    -    -    -    -
    # changer.start_accept      -    -    -    -    -    -    -    -    -    -
    # changer.stop_accept       -    -    +    -    -    -    -    -    -    -
    # changer.dispense_amount   -    -    -    -    -    -    -    -    -    -


    def test_12(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        
        self.check_outputs()


    def test_13(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_14(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_stop_accept_expected_args_list=[()])
        

    def test_15(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        
        self.check_outputs(fsm_initialized_expected_args_list=[()])


    def test_16_21(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        self.changer_fsm.start_accept()
        self.changer_fsm.stop_accept()
        self.changer_fsm.start_dispense(amount=10)
        self.changer_fsm.stop_dispense()
        
        # delays until changer.dispense_amount executed
        time.sleep(1)

        self.check_outputs()


    #                          22   23   24   25   26   27   28   29   30   31
    # inputs
    # fsm.state("OFF",         ERR  ERR  ERR  ERR  ERR  ERR  ERR  ERR  ERR  ERR
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WC",
    #          "DA")                
    # changer.online            +
    # changer.offline                +
    # changer.error                       +
    # changer.initialized                      +
    # changer.coin_in                               +
    # changer.coin_out                                   +
    # start_accept                                            +
    # stop_accept                                                  +
    # start_dispense                                                    +
    # stop_dispense                                                          +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    -    -    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -    -    
    # fsm_listener.coin_in      -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed    -    -    -    -    -    -    -    -    -    -
    # changer.start_accept      -    -    -    -    -    -    -    -    -    -
    # changer.stop_accept       -    -    -    -    -    -    -    -    -    -
    # changer.dispense_amount   -    -    -    -    -    -    -    -    -    -

    def test_22(self):
        self.set_fsm_state_error()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        
        self.changer_fsm.stop_dispense()


    def test_23(self):
        self.set_fsm_state_error()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_24_31(self):
        self.set_fsm_state_error()

        dispatcher.send_minimal(
            sender=self.changer, signal='error', error_code='12', error_text='error_12')
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=10)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=10)
        self.changer_fsm.start_accept()
        self.changer_fsm.stop_accept()
        self.changer_fsm.start_dispense(amount=10)
        self.changer_fsm.stop_dispense()
        
        # delays until changer.dispense_amount executed
        time.sleep(1)
        
        self.check_outputs()


    #                          32   33   34   35   36   37   38   39   40   41
    # inputs
    # fsm.state("OFF",         RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY  RDY
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WC",
    #          "DA")                
    # changer.online            +
    # changer.offline                +
    # changer.error                       +
    # changer.initialized                      +
    # changer.coin_in                               +
    # changer.coin_out                                   +
    # start_accept                                            +
    # stop_accept                                                  +
    # start_dispense                                                    +
    # stop_dispense                                                          +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    +    -    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -    -    
    # fsm_listener.coin_in      -    -    -    -    +    -    -    -    -    -
    # fsm_listener.dispensed    -    -    -    -    -    -    -    -    -    -
    # changer.start_accept      -    -    -    -    -    -    +    -    -    -
    # changer.stop_accept       -    -    +    -    -    -    -    -    -    -
    # changer.dispense_amount   -    -    -    -    -    -    -    -    +    -


    def test_32(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')

        self.check_outputs()


    def test_33(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_34(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_stop_accept_expected_args_list=[()])


    def test_35(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        
        self.check_outputs()
        
        
    def test_36(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=10)
        
        self.check_outputs(fsm_coin_in_expected_args_list=[({'amount':10},)],
                           changer_stop_accept_expected_args_list=[()])


    def test_37(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=10)

        self.check_outputs()
        
        
    def test_38(self):
        self.set_fsm_state_initialized()

        self.changer_fsm.start_accept()
        
        self.check_outputs(changer_start_accept_expected_args_list=[()])
        
        
    def test_39(self):
        self.set_fsm_state_initialized()

        self.changer_fsm.stop_accept()
        
        self.check_outputs()
        
        
    def test_40(self):
        self.set_fsm_state_initialized()

        self.changer_fsm.start_dispense(amount=10)
        
        # delays until changer.dispense_amount executed
        time.sleep(1)
        
        self.check_outputs(changer_dispense_amount_expected_args_list=[((10,),)])
        
        
    def test_41(self):
        self.set_fsm_state_initialized()

        self.changer_fsm.stop_dispense()
        
        self.check_outputs()
        

    #                          42   43   44   45   46   47   48   49   50   51
    # inputs
    # fsm.state("OFF",         WC   WC   WC   WC   WC   WC   WC   WC   WC   WC
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WC",
    #          "DA")                
    # changer.online            +
    # changer.offline                +
    # changer.error                       +
    # changer.initialized                      +
    # changer.coin_in                               +
    # changer.coin_out                                   +
    # start_accept                                            +
    # stop_accept                                                  +
    # start_dispense                                                    +
    # stop_dispense                                                          +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    +    -    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -    -
    # fsm_listener.coin_in      -    -    -    -    +    -    -    -    -    -
    # fsm_listener.dispensed    -    -    -    -    -    -    -    -    -    -
    # changer.start_accept      -    -    -    -    -    -    -    -    -    -
    # changer.stop_accept       -    -    +    -    +    -    -    +    -    -
    # changer.dispense_amount   -    -    -    -    -    -    -    -    -    -

    def test_42(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        
        self.check_outputs()


    def test_43(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_44(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_stop_accept_expected_args_list=[()])


    def test_45(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        
        self.check_outputs()


    def test_46(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=10)
        
        self.check_outputs(fsm_coin_in_expected_args_list=[({'amount':10},)],
                       changer_stop_accept_expected_args_list=[()])


    def test_47_48(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=10)
        self.changer_fsm.start_accept()
        
        self.check_outputs()


    def test_49(self):
        self.set_fsm_state_wait_coin()

        self.changer_fsm.stop_accept()
        
        self.check_outputs(changer_stop_accept_expected_args_list=[()])


    def test_50_51(self):
        self.set_fsm_state_wait_coin()

        self.changer_fsm.start_dispense(amount=10)
        self.changer_fsm.stop_dispense()
        
        # delays until changer.dispense_amount executed
        time.sleep(1)
        
        self.check_outputs()


    #                          52   53   54   55   56   57   58   59   60   61   62   63   64   65   66   67
    # inputs
    # fsm.state("OFF",         DA   DA   DA   DA   DA   DA   DA   DA   DA   DA   DA   DA   DA   DA   DA   DA
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WC",
    #          "DA")                
    # changer.online            +
    # changer.offline                +
    # changer.error                       +
    # changer.initialized                      +
    # changer.coin_in                               +
    # changer.coin_out: not_dispensed                    +
    # changer.coin_out: dispensed                             +    +    +    +
    # start_accept                                                                +
    # stop_accept                                                                      +
    # start_dispense                                                                        +
    # stop_dispense                                                                              +    +    +
    #
    # outputs
    # fsm_listener.online       -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.offline      -    +    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.error        -    -    +    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.ready        -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.coin_in      -    -    -    -    +    -    -    -    -    -    -    -    -    -    -    -
    # fsm_listener.dispensed    -    -    -    -    -    -    +    +    +    +    -    -    -    +    +    +
    # changer.start_accept      -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -
    # changer.stop_accept       -    -    +    -    +    -    -    -    -    -    -    -    -    -    -    -
    # changer.dispense_amount   -    -    -    -    -    -    -    -    -    -    -    -    -    -    -    -


    def test_52(self):
        self.set_fsm_state_dispense_amount()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        
        self.check_outputs()


    def test_53(self):
        self.set_fsm_state_dispense_amount()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        self.check_outputs(fsm_offline_expected_args_list=[()])


    def test_54(self):
        self.set_fsm_state_dispense_amount()

        dispatcher.send_minimal(
            sender=self.changer, signal='error', error_code=12, error_text='error_12')
        
        self.check_outputs(fsm_error_expected_args_list=[({'error_code':12, 'error_text':'error_12'},)],
                           changer_stop_accept_expected_args_list=[()])


    def test_55(self):
        self.set_fsm_state_dispense_amount()

        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        
        self.check_outputs()


    def test_56(self):
        self.set_fsm_state_dispense_amount()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=10)
        
        self.check_outputs(fsm_coin_in_expected_args_list=[({'amount':10},)],
                       changer_stop_accept_expected_args_list=[()])


    def test_57(self):
        self.set_fsm_state_dispense_amount(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=8)
        
        self.check_outputs()


    def test_58(self):
        self.set_fsm_state_dispense_amount(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=8)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        
        self.check_outputs(fsm_amount_dispensed_expected_args_list=[({'amount':10},)])


    def test_59(self):
        self.set_fsm_state_dispense_amount(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=8)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=2)
        
        self.check_outputs(fsm_amount_dispensed_expected_args_list=[({'amount':11},)])

    def test_60(self):
        self.set_fsm_state_dispense_amount(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=10)
        
        self.check_outputs(fsm_amount_dispensed_expected_args_list=[({'amount':10},)])


    def test_61(self):
        self.set_fsm_state_dispense_amount(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=11)
        
        self.check_outputs(fsm_amount_dispensed_expected_args_list=[({'amount':11},)])


    def test_62_64(self):
        self.set_fsm_state_dispense_amount()

        self.changer_fsm.start_accept()
        self.changer_fsm.stop_accept()
        self.changer_fsm.start_dispense()
        
        # delays until changer.dispense_amount executed
        time.sleep(1)
        
        self.check_outputs()


    def test_65(self):
        self.set_fsm_state_dispense_amount(10)

        self.changer_fsm.stop_dispense()
        
        self.check_outputs(fsm_amount_dispensed_expected_args_list=[({'amount':0,},)])


    def test_66(self):
        self.set_fsm_state_dispense_amount(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)

        self.changer_fsm.stop_dispense()
        
        self.check_outputs(fsm_amount_dispensed_expected_args_list=[({'amount':1,},)])


    def test_67(self):
        self.set_fsm_state_dispense_amount(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=8)

        self.changer_fsm.stop_dispense()
        
        self.check_outputs(fsm_amount_dispensed_expected_args_list=[({'amount':9,},)])
        
        
    def set_fsm_state_online(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        self.fsm_listener.online.reset_mock()
        
        
    def set_fsm_state_error(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        self.fsm_listener.online.reset_mock()
        dispatcher.send_minimal(
            sender=self.changer, signal='error', error_code='12', error_text='error_12')
        self.fsm_listener.error.reset_mock()
        self.changer.stop_accept.reset_mock()
        
        
    def set_fsm_state_initialized(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        self.fsm_listener.online.reset_mock()
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        self.fsm_listener.initialized.reset_mock()


    def set_fsm_state_wait_coin(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        self.fsm_listener.online.reset_mock()
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        self.fsm_listener.initialized.reset_mock()
        self.changer_fsm.start_accept()
        self.changer.start_accept.reset_mock()


    def set_fsm_state_dispense_amount(self, amount=10):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        self.fsm_listener.online.reset_mock()
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        self.fsm_listener.initialized.reset_mock()
        self.changer_fsm.start_dispense(amount=amount)
        
        # delays until changer.dispense_amount executed
        time.sleep(1)
        self.changer.dispense_amount.reset_mock()

            
    def check_outputs(self,
                      fsm_online_expected_args_list=[],
                      fsm_offline_expected_args_list=[],
                      fsm_error_expected_args_list=[],
                      fsm_initialized_expected_args_list=[],
                      fsm_coin_in_expected_args_list=[],
                      fsm_amount_dispensed_expected_args_list=[],
                      changer_start_accept_expected_args_list=[],
                      changer_stop_accept_expected_args_list=[],
                      changer_dispense_amount_expected_args_list=[]):
        self.assertEquals(fsm_online_expected_args_list, self.fsm_listener.online.call_args_list)
        self.assertEquals(fsm_offline_expected_args_list, self.fsm_listener.offline.call_args_list)
        self.assertEquals(fsm_error_expected_args_list, self.fsm_listener.error.call_args_list)
        self.assertEquals(fsm_initialized_expected_args_list, self.fsm_listener.initialized.call_args_list)
        self.assertEquals(fsm_coin_in_expected_args_list, self.fsm_listener.coin_in.call_args_list)
        self.assertEquals(fsm_amount_dispensed_expected_args_list, self.fsm_listener.amount_dispensed.call_args_list)
        self.assertEquals(changer_start_accept_expected_args_list, self.changer.start_accept.call_args_list)
        self.assertEquals(changer_stop_accept_expected_args_list, self.changer.stop_accept.call_args_list)
        self.assertEquals(changer_dispense_amount_expected_args_list, self.changer.dispense_amount.call_args_list)
            
