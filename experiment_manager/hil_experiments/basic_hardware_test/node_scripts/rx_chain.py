#!/usr/bin/env python3

# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#

# GNU Radio Python Flow Graph
# Title: RX Flowgraph
# Author: maity
# GNU Radio version: 3.10.12.0

import json
import os
import sys
import signal
import threading

from gnuradio import blocks
from gnuradio import gr
from gnuradio import uhd

# ============================================================
# Parameter Loading
# ============================================================


def load_parameters():

    # rx_chain.py is inside:
    #
    # <experiment_id>/node34/rx_chain.py
    #
    # parameters.json is inside:
    #
    # <experiment_id>/parameters.json

    experiment_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    parameter_file = os.path.join(experiment_dir, "parameters.json")

    print(f"Loading parameters from: {parameter_file}")

    if not os.path.isfile(parameter_file):

        raise FileNotFoundError(f"parameters.json not found: {parameter_file}")

    with open(parameter_file, "r", encoding="utf-8") as f:

        parameters = json.load(f)

    print("Loaded parameters:")
    print(json.dumps(parameters, indent=2))

    return parameters


# ============================================================
# RX Flowgraph
# ============================================================


class rx_chain(gr.top_block):

    def __init__(self):

        gr.top_block.__init__(self, "RX Flowgraph", catch_exceptions=True)

        self.flowgraph_started = threading.Event()

        # ----------------------------------------------------
        # Load parameters
        # ----------------------------------------------------

        parameters = load_parameters()

        # ----------------------------------------------------
        # Variables
        # ----------------------------------------------------

        self.samp_rate = samp_rate = float(parameters.get("sample_rate", 1000000))

        self.duration = duration = float(parameters.get("duration", 1))

        self.gain = gain = float(parameters.get("gain", 0))

        self.center_freq = center_freq = float(parameters.get("center_frequency", 0))

        # If capture_samples exists in parameters.json, use it. Otherwise: capture_samples = sample_rate * duration

        if "capture_samples" in parameters:

            self.capture_sample = capture_sample = int(parameters["capture_samples"])

        else:

            self.capture_sample = capture_sample = int(samp_rate * duration)

        # RX configuration

        print()
        print("RX configuration:")
        print(f"  Sample rate     : {samp_rate}")
        print(f"  Center frequency: {center_freq}")
        print(f"  Gain            : {gain}")
        print(f"  Duration        : {duration}")
        print(f"  Capture samples : {capture_sample}")
        print()

        # ====================================================
        # Blocks
        # ====================================================

        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                args="",
                channels=list(range(0, 1)),
            ),
        )

        self.uhd_usrp_source_0.set_samp_rate(samp_rate)

        self.uhd_usrp_source_0.set_center_freq(center_freq, 0)

        self.uhd_usrp_source_0.set_antenna("RX2", 0)

        self.uhd_usrp_source_0.set_gain(gain, 0)

        # ----------------------------------------------------
        # Head
        # ----------------------------------------------------

        self.blocks_head_0 = blocks.head(gr.sizeof_gr_complex * 1, capture_sample)

        # ----------------------------------------------------
        # File sink
        #
        # Save rx.iq in experiment root directory.
        #
        # <experiment_id>/rx.iq
        # ----------------------------------------------------

        experiment_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.rx_file = os.path.join(experiment_dir, "rx.iq")

        print(f"RX output file: {self.rx_file}")

        self.blocks_file_sink_0 = blocks.file_sink(
            gr.sizeof_gr_complex * 1, self.rx_file, False
        )

        self.blocks_file_sink_0.set_unbuffered(False)

        # ====================================================
        # Connections
        # ====================================================

        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_head_0, 0))

        self.connect((self.blocks_head_0, 0), (self.blocks_file_sink_0, 0))

    # ========================================================
    # Getters / Setters
    # ========================================================

    def get_samp_rate(self):

        return self.samp_rate

    def set_samp_rate(self, samp_rate):

        self.samp_rate = samp_rate

        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_duration(self):

        return self.duration

    def set_duration(self, duration):

        self.duration = duration

        self.set_capture_sample(int(self.samp_rate * self.duration))

    def get_gain(self):

        return self.gain

    def set_gain(self, gain):

        self.gain = gain

        self.uhd_usrp_source_0.set_gain(self.gain, 0)

    def get_center_freq(self):

        return self.center_freq

    def set_center_freq(self, center_freq):

        self.center_freq = center_freq

        self.uhd_usrp_source_0.set_center_freq(self.center_freq, 0)

    def get_capture_sample(self):

        return self.capture_sample

    def set_capture_sample(self, capture_sample):

        self.capture_sample = capture_sample

        self.blocks_head_0.set_length(self.capture_sample)


# ============================================================
# Main
# ============================================================


def main(top_block_cls=rx_chain, options=None):

    print("Starting RX flowgraph...")

    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):

        print("Stopping RX flowgraph...")

        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)

    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.flowgraph_started.set()

    print("RX flowgraph running.")

    tb.wait()

    print("RX flowgraph finished.")

    print(
        "::RESULT::"
        + json.dumps(
            {
                "status": "passed",
                "metrics": {
                    "capture_samples": tb.get_capture_sample(),
                    "sample_rate": tb.get_samp_rate(),
                },
            }
        )
    )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    main()
