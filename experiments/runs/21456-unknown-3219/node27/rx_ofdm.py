#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: OFDM Rx
# Description: Example of an OFDM receiver
# GNU Radio version: 3.10.12.0

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import uhd
import time
from gnuradio.digital.utils import tagged_streams
import threading

# Added for parameterization.
import json
import os


# Added for parameterization.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# Added for parameterization.
def load_parameters():
    parameters_path = os.path.abspath(
        os.path.join(
            SCRIPT_DIR,
            "..",
            "parameters.json",
        )
    )

    print(f"Loading parameters from: {parameters_path}")

    if not os.path.isfile(parameters_path):
        raise FileNotFoundError(
            f"parameters.json not found: {parameters_path}"
        )

    with open(parameters_path, "r", encoding="utf-8") as file:
        parameters = json.load(file)

    if not isinstance(parameters, dict):
        raise ValueError(
            "parameters.json must contain a JSON object"
        )

    print("Loaded parameters:")
    print(json.dumps(parameters, indent=2))

    return parameters


class rx_ofdm(gr.top_block):

    def __init__(self, parameters):
        gr.top_block.__init__(self, "OFDM Rx", catch_exceptions=True)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.pilot_symbols = pilot_symbols = (
            (
                1,
                1,
                1,
                -1,
            ),
        )
        self.pilot_carriers = pilot_carriers = (
            (
                -21,
                -7,
                7,
                21,
            ),
        )
        self.payload_mod = payload_mod = digital.constellation_qpsk()
        self.packet_length_tag_key = packet_length_tag_key = "packet_len"

        self.occupied_carriers = occupied_carriers = (
            (
                -26,
                -25,
                -24,
                -23,
                -22,
                -20,
                -19,
                -18,
                -17,
                -16,
                -15,
                -14,
                -13,
                -12,
                -11,
                -10,
                -9,
                -8,
                -6,
                -5,
                -4,
                -3,
                -2,
                -1,
                1,
                2,
                3,
                4,
                5,
                6,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                22,
                23,
                24,
                25,
                26,
            ),
        )

        # IMPORTANT:
        # TX uses packet_header_ofdm with:
        #
        # len_tag_key="packet_len"
        # frame_len_tag_key="packet_len"
        #
        # Therefore RX uses the same values.
        self.length_tag_key = length_tag_key = "packet_len"

        self.header_mod = header_mod = digital.constellation_bpsk()

        # Same FFT length as TX.
        self.fft_len = fft_len = 64

        self.sync_word2 = sync_word2 = [
            0j,
            0j,
            0j,
            0j,
            0j,
            0j,
            (-1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            0j,
            (1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            (-1 + 0j),
            0j,
            0j,
            0j,
            0j,
            0j,
        ]

        self.sync_word1 = sync_word1 = [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.41421356,
            0.0,
            -1.41421356,
            0.0,
            1.41421356,
            0.0,
            -1.41421356,
            0.0,
            -1.41421356,
            0.0,
            -1.41421356,
            0.0,
            1.41421356,
            0.0,
            -1.41421356,
            0.0,
            1.41421356,
            0.0,
            -1.41421356,
            0.0,
            -1.41421356,
            0.0,
            -1.41421356,
            0.0,
            -1.41421356,
            0.0,
            1.41421356,
            0.0,
            -1.41421356,
            0.0,
            1.41421356,
            0.0,
            1.41421356,
            0.0,
            1.41421356,
            0.0,
            -1.41421356,
            0.0,
            1.41421356,
            0.0,
            1.41421356,
            0.0,
            1.41421356,
            0.0,
            -1.41421356,
            0.0,
            1.41421356,
            0.0,
            1.41421356,
            0.0,
            1.41421356,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]

        # Parameterized from parameters.json.
        self.samp_rate = samp_rate = float(
            parameters["sample_rate"]
        )

        # Parameterized from parameters.json.
        self.rx_gain = rx_gain = float(
            parameters.get("rx_gain", 20)
        )

        self.payload_equalizer = payload_equalizer = (
            digital.ofdm_equalizer_simpledfe(
                fft_len,
                payload_mod.base(),
                occupied_carriers,
                pilot_carriers,
                pilot_symbols,
                1,
            )
        )

        # This is only a default variable.
        # Actual packet length comes from the received header.
        self.packet_len = packet_len = int(
            parameters.get("packet_len", 96)
        )

        # MUST match TX packet_header_ofdm.
        self.header_formatter = header_formatter = (
            digital.packet_header_ofdm(
                occupied_carriers,
                n_syms=1,
                len_tag_key=packet_length_tag_key,
                frame_len_tag_key=length_tag_key,
                bits_per_header_sym=header_mod.bits_per_symbol(),
                bits_per_payload_sym=payload_mod.bits_per_symbol(),
                scramble_header=False,
            )
        )

        self.header_equalizer = header_equalizer = (
            digital.ofdm_equalizer_simpledfe(
                fft_len,
                header_mod.base(),
                occupied_carriers,
                pilot_carriers,
                pilot_symbols,
            )
        )

        # Parameterized from parameters.json.
        self.center_freq = center_freq = float(
            parameters["center_frequency"]
        )

        # Parameterized output file.
        self.rx_output_file = rx_output_file = parameters.get(
            "rx_output_file",
            "rx_payload.bin",
        )

        ##################################################
        # RX configuration
        ##################################################

        print("\nRX configuration:")
        print(f"  Sample rate     : {self.samp_rate}")
        print(f"  Center frequency: {self.center_freq}")
        print(f"  Gain            : {self.rx_gain}")
        print(f"  Output file     : {self.rx_output_file}")
        print(f"  FFT length      : {self.fft_len}")
        print(f"  CP length       : {self.fft_len // 4}")
        print(f"  Packet tag      : {self.packet_length_tag_key}")
        print(f"  Frame tag       : {self.length_tag_key}")
        print("  Header symbols  : 1")
        print("  Payload modulation: QPSK")
        print("  Header modulation : BPSK")

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                args="",
                channels=list(range(0, 1)),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_source_0.set_center_freq(center_freq, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_gain(rx_gain, 0)

        self.fft_vxx_1 = fft.fft_vcc(
            fft_len,
            True,
            (),
            True,
            1,
        )

        self.fft_vxx_0 = fft.fft_vcc(
            fft_len,
            True,
            (),
            True,
            1,
        )

        self.digital_packet_headerparser_b_0 = (
            digital.packet_headerparser_b(
                header_formatter.base()
            )
        )

        self.digital_ofdm_sync_sc_cfb_0 = (
            digital.ofdm_sync_sc_cfb(
                fft_len,
                (fft_len // 4),
                False,
                0.9,
            )
        )

        self.digital_ofdm_serializer_vcc_payload = (
            digital.ofdm_serializer_vcc(
                fft_len,
                occupied_carriers,
                length_tag_key,
                packet_length_tag_key,
                1,
                "",
                True,
            )
        )

        self.digital_ofdm_serializer_vcc_header = (
            digital.ofdm_serializer_vcc(
                fft_len,
                occupied_carriers,
                length_tag_key,
                "",
                0,
                "",
                True,
            )
        )

        self.digital_ofdm_frame_equalizer_vcvc_1 = (
            digital.ofdm_frame_equalizer_vcvc(
                payload_equalizer.base(),
                (fft_len // 4),
                length_tag_key,
                True,
                0,
            )
        )

        self.digital_ofdm_frame_equalizer_vcvc_0 = (
            digital.ofdm_frame_equalizer_vcvc(
                header_equalizer.base(),
                (fft_len // 4),
                length_tag_key,
                True,
                1,
            )
        )

        self.digital_ofdm_chanest_vcvc_0 = (
            digital.ofdm_chanest_vcvc(
                sync_word1,
                sync_word2,
                1,
                0,
                3,
                False,
            )
        )

        self.digital_header_payload_demux_0 = (
            digital.header_payload_demux(
                3,
                fft_len,
                (fft_len // 4),
                "packet_len",
                "",
                True,
                gr.sizeof_gr_complex,
                "rx_time",
                samp_rate,
                (),
                0,
            )
        )

        self.digital_crc32_bb_0 = digital.crc32_bb(
            True,
            packet_length_tag_key,
            True,
        )

        self.digital_constellation_decoder_cb_1 = (
            digital.constellation_decoder_cb(
                payload_mod.base()
            )
        )

        self.digital_constellation_decoder_cb_0 = (
            digital.constellation_decoder_cb(
                header_mod.base()
            )
        )

        self.blocks_repack_bits_bb_0 = blocks.repack_bits_bb(
            payload_mod.bits_per_symbol(),
            8,
            packet_length_tag_key,
            True,
            gr.GR_LSB_FIRST,
        )

        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)

        self.blocks_file_sink_0 = blocks.file_sink(
            gr.sizeof_char * 1,
            rx_output_file,
            False,
        )

        self.blocks_file_sink_0.set_unbuffered(False)

        self.blocks_delay_0 = blocks.delay(
            gr.sizeof_gr_complex * 1,
            (fft_len + fft_len // 4),
        )

        self.analog_frequency_modulator_fc_0 = (
            analog.frequency_modulator_fc(
                (-2.0 / fft_len)
            )
        )

        ##################################################
        # Connections
        ##################################################

        self.msg_connect(
            (
                self.digital_packet_headerparser_b_0,
                "header_data",
            ),
            (
                self.digital_header_payload_demux_0,
                "header_data",
            ),
        )

        self.connect(
            (
                self.analog_frequency_modulator_fc_0,
                0,
            ),
            (
                self.blocks_multiply_xx_0,
                0,
            ),
        )

        self.connect(
            (
                self.blocks_delay_0,
                0,
            ),
            (
                self.blocks_multiply_xx_0,
                1,
            ),
        )

        self.connect(
            (
                self.blocks_multiply_xx_0,
                0,
            ),
            (
                self.digital_header_payload_demux_0,
                0,
            ),
        )

        self.connect(
            (
                self.blocks_repack_bits_bb_0,
                0,
            ),
            (
                self.digital_crc32_bb_0,
                0,
            ),
        )

        self.connect(
            (
                self.digital_constellation_decoder_cb_0,
                0,
            ),
            (
                self.digital_packet_headerparser_b_0,
                0,
            ),
        )

        self.connect(
            (
                self.digital_constellation_decoder_cb_1,
                0,
            ),
            (
                self.blocks_repack_bits_bb_0,
                0,
            ),
        )

        self.connect(
            (
                self.digital_crc32_bb_0,
                0,
            ),
            (
                self.blocks_file_sink_0,
                0,
            ),
        )

        self.connect(
            (
                self.digital_header_payload_demux_0,
                0,
            ),
            (
                self.fft_vxx_0,
                0,
            ),
        )

        self.connect(
            (
                self.digital_header_payload_demux_0,
                1,
            ),
            (
                self.fft_vxx_1,
                0,
            ),
        )

        self.connect(
            (
                self.digital_ofdm_chanest_vcvc_0,
                0,
            ),
            (
                self.digital_ofdm_frame_equalizer_vcvc_0,
                0,
            ),
        )

        self.connect(
            (
                self.digital_ofdm_frame_equalizer_vcvc_0,
                0,
            ),
            (
                self.digital_ofdm_serializer_vcc_header,
                0,
            ),
        )

        self.connect(
            (
                self.digital_ofdm_frame_equalizer_vcvc_1,
                0,
            ),
            (
                self.digital_ofdm_serializer_vcc_payload,
                0,
            ),
        )

        self.connect(
            (
                self.digital_ofdm_serializer_vcc_header,
                0,
            ),
            (
                self.digital_constellation_decoder_cb_0,
                0,
            ),
        )

        self.connect(
            (
                self.digital_ofdm_serializer_vcc_payload,
                0,
            ),
            (
                self.digital_constellation_decoder_cb_1,
                0,
            ),
        )

        self.connect(
            (
                self.digital_ofdm_sync_sc_cfb_0,
                0,
            ),
            (
                self.analog_frequency_modulator_fc_0,
                0,
            ),
        )

        self.connect(
            (
                self.digital_ofdm_sync_sc_cfb_0,
                1,
            ),
            (
                self.digital_header_payload_demux_0,
                1,
            ),
        )

        self.connect(
            (
                self.fft_vxx_0,
                0,
            ),
            (
                self.digital_ofdm_chanest_vcvc_0,
                0,
            ),
        )

        self.connect(
            (
                self.fft_vxx_1,
                0,
            ),
            (
                self.digital_ofdm_frame_equalizer_vcvc_1,
                0,
            ),
        )

        self.connect(
            (
                self.uhd_usrp_source_0,
                0,
            ),
            (
                self.blocks_delay_0,
                0,
            ),
        )

        self.connect(
            (
                self.uhd_usrp_source_0,
                0,
            ),
            (
                self.digital_ofdm_sync_sc_cfb_0,
                0,
            ),
        )

    def get_pilot_symbols(self):
        return self.pilot_symbols

    def set_pilot_symbols(self, pilot_symbols):
        self.pilot_symbols = pilot_symbols
        self.set_header_equalizer(
            digital.ofdm_equalizer_simpledfe(
                self.fft_len,
                self.header_mod.base(),
                self.occupied_carriers,
                self.pilot_carriers,
                self.pilot_symbols,
            )
        )
        self.set_payload_equalizer(
            digital.ofdm_equalizer_simpledfe(
                self.fft_len,
                self.payload_mod.base(),
                self.occupied_carriers,
                self.pilot_carriers,
                self.pilot_symbols,
                1,
            )
        )

    def get_pilot_carriers(self):
        return self.pilot_carriers

    def set_pilot_carriers(self, pilot_carriers):
        self.pilot_carriers = pilot_carriers
        self.set_header_equalizer(
            digital.ofdm_equalizer_simpledfe(
                self.fft_len,
                self.header_mod.base(),
                self.occupied_carriers,
                self.pilot_carriers,
                self.pilot_symbols,
            )
        )
        self.set_payload_equalizer(
            digital.ofdm_equalizer_simpledfe(
                self.fft_len,
                self.payload_mod.base(),
                self.occupied_carriers,
                self.pilot_carriers,
                self.pilot_symbols,
                1,
            )
        )

    def get_payload_mod(self):
        return self.payload_mod

    def set_payload_mod(self, payload_mod):
        self.payload_mod = payload_mod

    def get_packet_length_tag_key(self):
        return self.packet_length_tag_key

    def set_packet_length_tag_key(self, packet_length_tag_key):
        self.packet_length_tag_key = packet_length_tag_key
        self.set_header_formatter(
            digital.packet_header_ofdm(
                self.occupied_carriers,
                n_syms=1,
                len_tag_key=self.packet_length_tag_key,
                frame_len_tag_key=self.length_tag_key,
                bits_per_header_sym=self.header_mod.bits_per_symbol(),
                bits_per_payload_sym=self.payload_mod.bits_per_symbol(),
                scramble_header=False,
            )
        )

    def get_occupied_carriers(self):
        return self.occupied_carriers

    def set_occupied_carriers(self, occupied_carriers):
        self.occupied_carriers = occupied_carriers
        self.set_header_equalizer(
            digital.ofdm_equalizer_simpledfe(
                self.fft_len,
                self.header_mod.base(),
                self.occupied_carriers,
                self.pilot_carriers,
                self.pilot_symbols,
            )
        )
        self.set_header_formatter(
            digital.packet_header_ofdm(
                self.occupied_carriers,
                n_syms=1,
                len_tag_key=self.packet_length_tag_key,
                frame_len_tag_key=self.length_tag_key,
                bits_per_header_sym=self.header_mod.bits_per_symbol(),
                bits_per_payload_sym=self.payload_mod.bits_per_symbol(),
                scramble_header=False,
            )
        )
        self.set_payload_equalizer(
            digital.ofdm_equalizer_simpledfe(
                self.fft_len,
                self.payload_mod.base(),
                self.occupied_carriers,
                self.pilot_carriers,
                self.pilot_symbols,
                1,
            )
        )

    def get_length_tag_key(self):
        return self.length_tag_key

    def set_length_tag_key(self, length_tag_key):
        self.length_tag_key = length_tag_key
        self.set_header_formatter(
            digital.packet_header_ofdm(
                self.occupied_carriers,
                n_syms=1,
                len_tag_key=self.packet_length_tag_key,
                frame_len_tag_key=self.length_tag_key,
                bits_per_header_sym=self.header_mod.bits_per_symbol(),
                bits_per_payload_sym=self.payload_mod.bits_per_symbol(),
                scramble_header=False,
            )
        )

    def get_header_mod(self):
        return self.header_mod

    def set_header_mod(self, header_mod):
        self.header_mod = header_mod

    def get_fft_len(self):
        return self.fft_len

    def set_fft_len(self, fft_len):
        self.fft_len = fft_len

        self.set_header_equalizer(
            digital.ofdm_equalizer_simpledfe(
                self.fft_len,
                self.header_mod.base(),
                self.occupied_carriers,
                self.pilot_carriers,
                self.pilot_symbols,
            )
        )

        self.set_payload_equalizer(
            digital.ofdm_equalizer_simpledfe(
                self.fft_len,
                self.payload_mod.base(),
                self.occupied_carriers,
                self.pilot_carriers,
                self.pilot_symbols,
                1,
            )
        )

        self.analog_frequency_modulator_fc_0.set_sensitivity(
            (-2.0 / self.fft_len)
        )

        self.blocks_delay_0.set_dly(
            int(self.fft_len + self.fft_len // 4)
        )

    def get_sync_word2(self):
        return self.sync_word2

    def set_sync_word2(self, sync_word2):
        self.sync_word2 = sync_word2

    def get_sync_word1(self):
        return self.sync_word1

    def set_sync_word1(self, sync_word1):
        self.sync_word1 = sync_word1

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(
            self.samp_rate
        )

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain
        self.uhd_usrp_source_0.set_gain(
            self.rx_gain,
            0,
        )

    def get_payload_equalizer(self):
        return self.payload_equalizer

    def set_payload_equalizer(self, payload_equalizer):
        self.payload_equalizer = payload_equalizer

    def get_packet_len(self):
        return self.packet_len

    def set_packet_len(self, packet_len):
        self.packet_len = packet_len

    def get_header_formatter(self):
        return self.header_formatter

    def set_header_formatter(self, header_formatter):
        self.header_formatter = header_formatter

    def get_header_equalizer(self):
        return self.header_equalizer

    def set_header_equalizer(self, header_equalizer):
        self.header_equalizer = header_equalizer

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.uhd_usrp_source_0.set_center_freq(
            self.center_freq,
            0,
        )


def main(top_block_cls=rx_ofdm, options=None):
    # Added for parameterization.
    try:
        parameters = load_parameters()
        tb = top_block_cls(parameters)
    except Exception as error:
        print(
            f"Failed to initialize RX flowgraph: {error}",
            file=sys.stderr,
        )
        sys.exit(1)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()
    tb.flowgraph_started.set()

    tb.wait()


if __name__ == "__main__":
    main()