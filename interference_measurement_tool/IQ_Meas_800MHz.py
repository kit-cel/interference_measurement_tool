#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Iq Meas 800Mhz
# Generated: Mon Feb  5 11:03:36 2018
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import time


class IQ_Meas_800MHz(gr.top_block):

    def __init__(self, outputfile='/home/messung/Tool/IQ_Temp/IQ.bin'):
        gr.top_block.__init__(self, "Iq Meas 800Mhz")

        ##################################################
        # Parameters
        ##################################################
        self.outputfile = outputfile

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = int(11e6)
        self.num_total_items = num_total_items = int(samp_rate)*10
        self.num_skip_head = num_skip_head = int(samp_rate / 2)
        self.last_output_buffer_size = last_output_buffer_size = int(samp_rate)*4
        self.center_freq = center_freq = 866.5e6

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join(("num_recv_frames=128,num_send_frames=128", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_subdev_spec("A:B", 0)
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(center_freq), 0)
        self.uhd_usrp_source_0.set_gain(20, 0)
        self.uhd_usrp_source_0.set_antenna('TX/RX', 0)
        self.uhd_usrp_source_0.set_bandwidth(10e6, 0)
        (self.uhd_usrp_source_0).set_min_output_buffer(55000000)
        self.root_raised_cosine_filter_0_0 = filter.fir_filter_ccf(1, firdes.root_raised_cosine(
        	1, samp_rate, 1e6, 1, 50))
        (self.root_raised_cosine_filter_0_0).set_min_output_buffer(55000000)
        self.blocks_tag_debug_0 = blocks.tag_debug(gr.sizeof_gr_complex*1, '', ""); self.blocks_tag_debug_0.set_display(True)
        self.blocks_skiphead_0_0 = blocks.skiphead(gr.sizeof_gr_complex*1, num_skip_head)
        (self.blocks_skiphead_0_0).set_min_output_buffer(11000000)
        self.blocks_head_0_0 = blocks.head(gr.sizeof_gr_complex*1, num_total_items)
        (self.blocks_head_0_0).set_min_output_buffer(44000000)
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_gr_complex*1, '/home/messung/Documents/interference-measurement-tool/Tool/IQ_Temp/IQ.bin', False)
        self.blocks_file_sink_0_0.set_unbuffered(False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_head_0_0, 0), (self.blocks_file_sink_0_0, 0))
        self.connect((self.blocks_skiphead_0_0, 0), (self.blocks_head_0_0, 0))
        self.connect((self.root_raised_cosine_filter_0_0, 0), (self.blocks_skiphead_0_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_tag_debug_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.root_raised_cosine_filter_0_0, 0))

    def get_outputfile(self):
        return self.outputfile

    def set_outputfile(self, outputfile):
        self.outputfile = outputfile

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_num_total_items(int(self.samp_rate)*10)
        self.set_num_skip_head(int(self.samp_rate / 2))
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.root_raised_cosine_filter_0_0.set_taps(firdes.root_raised_cosine(1, self.samp_rate, 1e6, 1, 50))
        self.set_last_output_buffer_size(int(self.samp_rate)*4)

    def get_num_total_items(self):
        return self.num_total_items

    def set_num_total_items(self, num_total_items):
        self.num_total_items = num_total_items
        self.blocks_head_0_0.set_length(self.num_total_items)

    def get_num_skip_head(self):
        return self.num_skip_head

    def set_num_skip_head(self, num_skip_head):
        self.num_skip_head = num_skip_head

    def get_last_output_buffer_size(self):
        return self.last_output_buffer_size

    def set_last_output_buffer_size(self, last_output_buffer_size):
        self.last_output_buffer_size = last_output_buffer_size

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(self.center_freq), 0)


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    parser.add_option(
        "", "--outputfile", dest="outputfile", type="string", default='/home/messung/Tool/IQ_Temp/IQ.bin',
        help="Set outputfile [default=%default]")
    return parser


def main(top_block_cls=IQ_Meas_800MHz, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    tb = top_block_cls(outputfile=options.outputfile)
    tb.start()
    tb.wait()


if __name__ == '__main__':
    main()
