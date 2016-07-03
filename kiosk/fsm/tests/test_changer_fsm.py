
from louie import dispatcher

from twisted.internet import reactor, defer, task

#from unittest import TestCase
from twisted.trial import unittest

from kiosk.fsm.changer_fsm import ChangerFSM


try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock
    

class TestChangerFsm(unittest.TestCase):
    
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
        
        dispatcher.connect(self.fsm_listener.online,
                           sender=self.changer_fsm, signal='online')
        dispatcher.connect(self.fsm_listener.offline, 
                           sender=self.changer_fsm, signal='offline')
        dispatcher.connect(self.fsm_listener.initialized, 
                           sender=self.changer_fsm, signal='initialized')
        dispatcher.connect(self.fsm_listener.error, 
                           sender=self.changer_fsm, signal='error')
        dispatcher.connect(self.fsm_listener.coin_in, 
                           sender=self.changer_fsm, signal='coin_in')
        dispatcher.connect(self.fsm_listener.amount_dispensed, 
                           sender=self.changer_fsm, signal='amount_dispensed')


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


    @defer.inlineCallbacks
    def test_1_on_offline(self):
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_2_changer_online_on_offline(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')

        yield self.check_outputs_defer(fsm_online_expected=[()])
        

    @defer.inlineCallbacks
    def test_3_changer_offline_on_offline(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_4_changer_error_on_offline(self):
        dispatcher.send_minimal(
            sender=self.changer, 
            signal='error', error_code=12, error_text="error_12")
        
        yield self.check_outputs_defer()
    
    
    @defer.inlineCallbacks
    def test_5_changer_initialized_on_offline(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_6_coin_in_on_offline(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=1)
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_7_coin_out_on_offline(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_8_start_accept_on_offline(self):
        self.changer_fsm.start_accept()
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_9_stop_accept_on_offline(self):
        self.changer_fsm.stop_accept()
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_10_start_dispense_on_offline(self):
        self.changer_fsm.start_dispense(amount=20)
        
        yield self.check_outputs_defer(
                   fsm_amount_dispensed_expected=[({'amount': 0,},)])


    @defer.inlineCallbacks
    def test_11_stop_dispense_on_offline(self):
        self.changer_fsm.stop_dispense()
        
        yield self.check_outputs_defer()


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


    @defer.inlineCallbacks
    def test_12_changer_online_on_online(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_13_changer_offline_on_online(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        yield self.check_outputs_defer(fsm_offline_expected=[()])


    @defer.inlineCallbacks
    def test_14_changer_error_on_online(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer,
            signal='error', error_code=12, error_text='error_12')
        
        yield self.check_outputs_defer(
           fsm_error_expected=[({'error_code':12, 'error_text':'error_12'},)],
           changer_stop_accept_expected=[()])
        

    @defer.inlineCallbacks
    def test_15_changer_initialized_on_online(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        
        yield self.check_outputs_defer(fsm_initialized_expected=[()])


    @defer.inlineCallbacks
    def test_16_coin_in_on_online(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=1)
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_17_coin_out_on_online(self):
        self.set_fsm_state_online()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_18_start_accept_on_online(self):
        self.set_fsm_state_online()

        self.changer_fsm.start_accept()
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_19_stop_accept_on_online(self):
        self.set_fsm_state_online()

        self.changer_fsm.stop_accept()
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_20_start_dispense_on_online(self):
        self.set_fsm_state_online()

        self.changer_fsm.start_dispense(amount=10)
        
        yield self.check_outputs_defer(
                           fsm_amount_dispensed_expected=[({'amount': 0,},)])


    @defer.inlineCallbacks
    def test_21_stop_dispense_on_online(self):
        self.set_fsm_state_online()

        self.changer_fsm.stop_dispense()
        
        yield self.check_outputs_defer()


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

    @defer.inlineCallbacks
    def test_22_changer_online_on_error(self):
        self.set_fsm_state_error()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_23_changer_offline_on_error(self):
        self.set_fsm_state_error()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        yield self.check_outputs_defer(fsm_offline_expected=[()])


    @defer.inlineCallbacks
    def test_24_changer_error_on_error(self):
        self.set_fsm_state_error()

        dispatcher.send_minimal(
            sender=self.changer, 
            signal='error', error_code='12', error_text='error_12')
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_25_changer_initialized_on_error(self):
        self.set_fsm_state_error()

        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_26_coin_in_on_error(self):
        self.set_fsm_state_error()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=10)
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_27_coin_out_on_error(self):
        self.set_fsm_state_error()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=10)
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_28_start_accept_on_error(self):
        self.set_fsm_state_error()

        self.changer_fsm.start_accept()
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_29_stop_accept_on_error(self):
        self.set_fsm_state_error()

        self.changer_fsm.stop_accept()
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_30_start_dispense_on_error(self):
        self.set_fsm_state_error()

        self.changer_fsm.start_dispense(amount=10)
        
        yield self.check_outputs_defer(
                       fsm_amount_dispensed_expected=[({'amount': 0,},)])


    @defer.inlineCallbacks
    def test_31_stop_dispense_on_error(self):
        self.set_fsm_state_error()

        self.changer_fsm.stop_dispense()
        
        yield self.check_outputs_defer()


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


    @defer.inlineCallbacks
    def test_32_changer_online_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')

        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_33_changer_offline_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        yield self.check_outputs_defer(fsm_offline_expected=[()])


    @defer.inlineCallbacks
    def test_34_changer_error_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, 
            signal='error', error_code=12, error_text='error_12')
        
        yield self.check_outputs_defer(
           fsm_error_expected=[({'error_code':12, 'error_text':'error_12'},)],
           changer_stop_accept_expected=[()])


    @defer.inlineCallbacks
    def test_35_changer_initialized_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        
        yield self.check_outputs_defer()
        
        
    @defer.inlineCallbacks
    def test_36_coin_in_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=10)
        
        yield self.check_outputs_defer(fsm_coin_in_expected=[({'amount':10},)],
                           changer_stop_accept_expected=[()])


    @defer.inlineCallbacks
    def test_37_coin_out_on_ready(self):
        self.set_fsm_state_initialized()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=10)

        yield self.check_outputs_defer()
        
        
    @defer.inlineCallbacks
    def test_38_start_accept_on_ready(self):
        self.set_fsm_state_initialized()

        self.changer_fsm.start_accept()
        
        yield self.check_outputs_defer(changer_start_accept_expected=[()])
        
        
    @defer.inlineCallbacks
    def test_39_stop_accept_on_ready(self):
        self.set_fsm_state_initialized()

        self.changer_fsm.stop_accept()
        
        yield self.check_outputs_defer()
        
    @defer.inlineCallbacks
    def test_40_start_dispense_on_ready(self):
        self.set_fsm_state_initialized()

        self.changer_fsm.start_dispense(amount=10)
        
        yield self.check_outputs_defer(
                   changer_dispense_amount_expected=[((10,),)])
    

    @defer.inlineCallbacks
    def test_41_stop_dispense_on_ready(self):
        self.set_fsm_state_initialized()

        self.changer_fsm.stop_dispense()
        
        yield self.check_outputs_defer()
        

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

    @defer.inlineCallbacks
    def test_42_changer_online_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_43_changer_offline_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
        
        yield self.check_outputs_defer(fsm_offline_expected=[()])


    @defer.inlineCallbacks
    def test_44_changer_error_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, 
            signal='error', error_code=12, error_text='error_12')
        
        yield self.check_outputs_defer(
           fsm_error_expected=[({'error_code':12, 'error_text':'error_12'},)],
           changer_stop_accept_expected=[()])


    @defer.inlineCallbacks
    def test_45_changer_initialized_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_46_coin_in_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=10)
        
        yield self.check_outputs_defer(fsm_coin_in_expected=[({'amount':10},)],
                       changer_stop_accept_expected=[()])


    @defer.inlineCallbacks
    def test_47_coin_out_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=10)
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_48_start_accept_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        self.changer_fsm.start_accept()
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_49_stop_accept_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        self.changer_fsm.stop_accept()
        
        yield self.check_outputs_defer(changer_stop_accept_expected=[()])


    @defer.inlineCallbacks
    def test_50_start_dispense_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        self.changer_fsm.start_dispense(amount=10)
        
        yield self.check_outputs_defer(changer_dispense_amount_expected=[((10,),)])


    @defer.inlineCallbacks
    def test_51_start_dispense_on_wait_coin(self):
        self.set_fsm_state_wait_coin()

        self.changer_fsm.stop_dispense()
        
        yield self.check_outputs_defer()


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


    @defer.inlineCallbacks
    def test_52_changer_online_on_dispense_amount(self):
        yield self.set_fsm_state_dispense_amount_defer()

        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_53_changer_offline_on_dispense_amount(self):
        yield self.set_fsm_state_dispense_amount_defer()

        dispatcher.send_minimal(
            sender=self.changer, signal='offline')
            
        yield self.check_outputs_defer(fsm_offline_expected=[()])


    @defer.inlineCallbacks
    def test_54_changer_error_on_dispense_amount(self):
        yield self.set_fsm_state_dispense_amount_defer()

        dispatcher.send_minimal(
            sender=self.changer, 
            signal='error', error_code=12, error_text='error_12')
            
        yield self.check_outputs_defer(
           fsm_error_expected=[({'error_code':12, 'error_text':'error_12'},)],
           changer_stop_accept_expected=[()])


    @defer.inlineCallbacks
    def test_55_changer_initialized_on_dispense_amount(self):
        yield self.set_fsm_state_dispense_amount_defer()

        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
            
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_56_coin_in_on_dispense_amount(self):
        yield self.set_fsm_state_dispense_amount_defer()

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_in', amount=10)
            
        yield self.check_outputs_defer(fsm_coin_in_expected=[({'amount':10},)],
                                       changer_stop_accept_expected=[()])


    @defer.inlineCallbacks
    def test_57_coin_out_on_dispense_amount(self):
        '''
        dispensed amount not enough
        '''
        yield self.set_fsm_state_dispense_amount_defer(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=8)
            
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_58_coin_out_on_dispense_amount(self):
        '''
        dispensed amount not enough
        '''
        yield self.set_fsm_state_dispense_amount_defer(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=8)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
            
        yield self.check_outputs_defer( 
                           fsm_amount_dispensed_expected=[({'amount':10},)])


    @defer.inlineCallbacks
    def test_59_coin_out_on_dispense_amount(self):
        '''
        dispensed amount not enough
        '''
        yield self.set_fsm_state_dispense_amount_defer(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=8)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=2)
            
        yield self.check_outputs_defer( 
                           fsm_amount_dispensed_expected=[({'amount':11},)])


    @defer.inlineCallbacks
    def test_60_coin_out_on_dispense_amount(self):
        '''
        dispensed amount not enough
        '''
        yield self.set_fsm_state_dispense_amount_defer(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=10)
            
        yield self.check_outputs_defer( 
                           fsm_amount_dispensed_expected=[({'amount':10},)])


    @defer.inlineCallbacks
    def test_61_coin_out_on_dispense_amount(self):
        yield self.set_fsm_state_dispense_amount_defer(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=11)
            
        yield self.check_outputs_defer(
                           fsm_amount_dispensed_expected=[({'amount':11},)])


    @defer.inlineCallbacks
    def test_62_start_accept_on_dispense_amount(self):
        yield self.set_fsm_state_dispense_amount_defer()

        self.changer_fsm.start_accept()
            
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_63_stop_accept_on_dispense_amount(self):
        yield self.set_fsm_state_dispense_amount_defer()

        self.changer_fsm.stop_accept()
            
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_64_start_dispense_on_dispense_amount(self):
        yield self.set_fsm_state_dispense_amount_defer()

        self.changer_fsm.start_dispense()
            
        yield self.check_outputs_defer()


    @defer.inlineCallbacks
    def test_65_stop_dispense_on_dispense_amount(self):
        '''
        no any amount dispensed before stopping
        '''
        yield self.set_fsm_state_dispense_amount_defer(10)

        self.changer_fsm.stop_dispense()
            
        yield self.check_outputs_defer(
                           fsm_amount_dispensed_expected=[({'amount':0,},)])


    @defer.inlineCallbacks
    def test_66_stop_dispense_on_dispense_amount(self):
        '''
        minimal amount dispensed before stopping
        '''
        yield self.set_fsm_state_dispense_amount_defer(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
    
        self.changer_fsm.stop_dispense()
            
        yield self.check_outputs_defer(
                           fsm_amount_dispensed_expected=[({'amount':1,},)])


    @defer.inlineCallbacks
    def test_67_stop_dispense_on_dispense_amount(self):
        '''
        some amount dispensed before stopping
        '''
        yield self.set_fsm_state_dispense_amount_defer(10)

        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=1)
        dispatcher.send_minimal(
            sender=self.changer, signal='coin_out', amount=8)
    
        self.changer_fsm.stop_dispense()
            
        yield self.check_outputs_defer(
                           fsm_amount_dispensed_expected=[({'amount':9,},)])

    #                          68
    # inputs
    # fsm.state("OFF",         RDY
    #          "ON",
    #          "ERR",
    #          "RDY",
    #          "WC",
    #          "DA")                
    # start_dispense(0)         +
    #
    # outputs
    # fsm_listener.online       -
    # fsm_listener.offline      -
    # fsm_listener.error        -
    # fsm_listener.ready        -
    # fsm_listener.coin_in      -
    # fsm_listener.dispensed    +
    # changer.start_accept      -
    # changer.stop_accept       -
    # changer.dispense_amount   -
    
    @defer.inlineCallbacks
    def test_68_start_zero_dispense_on_ready(self):
        self.set_fsm_state_initialized()

        self.changer_fsm.start_dispense(amount=0)
        
        yield self.check_outputs_defer(
                           fsm_amount_dispensed_expected=[({'amount':0},)])
    
        
    def set_fsm_state_online(self):
        dispatcher.send_minimal(
            sender=self.changer, signal='online')
        self.fsm_listener.online.reset_mock()
        
        
    def set_fsm_state_error(self):
        self.set_fsm_state_online()
        dispatcher.send_minimal(
            sender=self.changer, 
            signal='error', error_code='12', error_text='error_12')
        self.fsm_listener.error.reset_mock()
        self.changer.stop_accept.reset_mock()
        
        
    def set_fsm_state_initialized(self):
        self.set_fsm_state_online()
        dispatcher.send_minimal(
            sender=self.changer, signal='initialized')
        self.fsm_listener.initialized.reset_mock()


    def set_fsm_state_wait_coin(self):
        self.set_fsm_state_initialized()
        self.changer_fsm.start_accept()
        self.changer.start_accept.reset_mock()


    def set_fsm_state_dispense_amount_defer(self, amount=10):
        self.set_fsm_state_initialized()
        self.changer_fsm.start_dispense(amount=amount)
        
        def callback_func(dont_care):
            self.changer.dispense_amount.reset_mock()

        return task.deferLater(reactor, 0, callback_func, None)

            
    def check_outputs_defer(self, sleep_sec=0,
                      fsm_online_expected=[],
                      fsm_offline_expected=[],
                      fsm_error_expected=[],
                      fsm_initialized_expected=[],
                      fsm_coin_in_expected=[],
                      fsm_amount_dispensed_expected=[],
                      changer_start_accept_expected=[],
                      changer_stop_accept_expected=[],
                      changer_dispense_amount_expected=[]):
        
        def callback_func(dont_care):
            self.assertEquals(fsm_online_expected, 
                              self.fsm_listener.online.call_args_list)
            self.assertEquals(fsm_offline_expected, 
                              self.fsm_listener.offline.call_args_list)
            self.assertEquals(fsm_error_expected, 
                              self.fsm_listener.error.call_args_list)
            self.assertEquals(fsm_initialized_expected, 
                              self.fsm_listener.initialized.call_args_list)
            self.assertEquals(fsm_coin_in_expected, 
                              self.fsm_listener.coin_in.call_args_list)
            self.assertEquals(fsm_amount_dispensed_expected, 
                              self.fsm_listener.amount_dispensed.call_args_list)
            self.assertEquals(changer_start_accept_expected, 
                              self.changer.start_accept.call_args_list)
            self.assertEquals(changer_stop_accept_expected, 
                              self.changer.stop_accept.call_args_list)
            self.assertEquals(changer_dispense_amount_expected, 
                              self.changer.dispense_amount.call_args_list)

        return task.deferLater(reactor, sleep_sec, callback_func, None)
            
