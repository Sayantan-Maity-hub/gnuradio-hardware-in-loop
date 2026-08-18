#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#

# GNU Radio Python Flow Graph
# Title: TX Flowgraph
# Author: maity
# GNU Radio version: 3.10.12.0

import json
import os
import signal
import sys
import threading

from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio import uhd


def load_parameters():
    """
    Load experiment parameters from parameters.json.

    Expected structure:

    {
        "sample_rate": 1000000,
        "center_frequency": 1000000,
        "gain": 20,
        "tone_frequency": 100000,
        "capture_samples": 1000000,
        "amplitude": 0.5
    }
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parameters_path = os.path.join(script_dir, "..", "parameters.json")

    parameters_path = os.path.abspath(parameters_path)

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


class tx_chain(gr.top_block):

    def __init__(self, parameters):
        gr.top_block.__init__(
            self,
            "TX Flowgraph",
            catch_exceptions=True,
        )

        self.flowgraph_started = threading.Event()

        ##################################################
        # Parameters
        ##################################################

        self.samp_rate = float(parameters["sample_rate"])

        self.center_freq = float(parameters["center_frequency"])

        self.gain = float(parameters["gain"])

        self.tone_frequency = float(parameters["tone_frequency"])

        self.amplitude = float(parameters.get("amplitude", 0.5))

        # Prefer capture_samples if explicitly provided. Otherwise calculate it from: sample_rate * duration

        if "capture_samples" in parameters:
            self.captured_samp = int(parameters["capture_samples"])

        elif "duration" in parameters:
            duration = float(parameters["duration"])

            self.captured_samp = int(self.samp_rate * duration)

        else:
            raise ValueError("parameters.json must contain either 'capture_samples' or 'duration'")

        print("\nTX configuration:")
        print(f"  Sample rate     : {self.samp_rate}")
        print(f"  Center frequency: {self.center_freq}")
        print(f"  Gain            : {self.gain}")
        print(f"  Tone frequency  : {self.tone_frequency}")
        print(f"  Amplitude       : {self.amplitude}")
        print(f"  Capture samples : {self.captured_samp}")

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                args="",
                channels=list(range(0, 1)),
            ),
            "",
        )

        self.uhd_usrp_sink_0.set_samp_rate(
            self.samp_rate
        )

        self.uhd_usrp_sink_0.set_time_unknown_pps(
            uhd.time_spec(0)
        )

        self.uhd_usrp_sink_0.set_center_freq(
            self.center_freq,
            0,
        )

        self.uhd_usrp_sink_0.set_antenna(
            "TX/RX",
            0,
        )

        self.uhd_usrp_sink_0.set_gain(
            self.gain,
            0,
        )

        self.blocks_head_0 = blocks.head(
            gr.sizeof_gr_complex,
            self.captured_samp,
        )

        self.analog_sig_source_x_0 = analog.sig_source_c(
            self.samp_rate,
            analog.GR_COS_WAVE,
            self.tone_frequency,
            self.amplitude,
            0,
            0,
        )

        ##################################################
        # Connections
        ##################################################

        self.connect(
            (self.analog_sig_source_x_0, 0),
            (self.blocks_head_0, 0),
        )

        self.connect(
            (self.blocks_head_0, 0),
            (self.uhd_usrp_sink_0, 0),
        )

    ##################################################
    # Getter / Setter methods
    ##################################################

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

        self.analog_sig_source_x_0.set_sampling_freq(
            self.samp_rate
        )

        self.uhd_usrp_sink_0.set_samp_rate(
            self.samp_rate
        )

    def get_tone_frequency(self):
        return self.tone_frequency

    def set_tone_frequency(self, tone_frequency):
        self.tone_frequency = tone_frequency

        self.analog_sig_source_x_0.set_frequency(
            self.tone_frequency
        )

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain

        self.uhd_usrp_sink_0.set_gain(
            self.gain,
            0,
        )

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq

        self.uhd_usrp_sink_0.set_center_freq(
            self.center_freq,
            0,
        )

    def get_amplitude(self):
        return self.amplitude

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude

        self.analog_sig_source_x_0.set_amplitude(
            self.amplitude
        )

    def get_captured_samp(self):
        return self.captured_samp

    def set_captured_samp(self, captured_samp):
        self.captured_samp = int(captured_samp)

        self.blocks_head_0.set_length(
            self.captured_samp
        )


def main(top_block_cls=tx_chain):

    try:
        parameters = load_parameters()

        tb = top_block_cls(parameters)

    except Exception as error:
        print(
            f"Failed to initialize TX flowgraph: {error}",
            file=sys.stderr,
        )
        sys.exit(1)

    def sig_handler(sig=None, frame=None):
        print("Stopping TX flowgraph...")

        try:
            tb.stop()
            tb.wait()
        except Exception as error:
            print(
                f"Error while stopping TX: {error}",
                file=sys.stderr,
            )

        sys.exit(0)

    signal.signal(
        signal.SIGINT,
        sig_handler,
    )

    signal.signal(
        signal.SIGTERM,
        sig_handler,
    )

    print("Starting TX flowgraph...")

    tb.start()
    tb.flowgraph_started.set()

    print("TX flowgraph running.")

    tb.wait()

    print("TX flowgraph finished.")

    print(
        '::RESULT::{"status":"passed","metrics":{}}'
    )


if __name__ == "__main__":
    main()