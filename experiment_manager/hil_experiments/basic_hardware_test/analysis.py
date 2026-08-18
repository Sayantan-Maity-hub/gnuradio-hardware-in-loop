#!/usr/bin/env python3

import json
import os

import numpy as np


def load_parameters(parameters_path):
    if not os.path.exists(parameters_path):
        return {}

    with open(
        parameters_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_analysis(samples, sample_rate, expected_frequency):
    """
    Analyze received complex IQ samples.

    Returns:
        dict containing signal metrics.
    """

    num_samples = len(samples)

    # Remove DC component

    samples = samples - np.mean(samples)

    # Average signal power
    power = np.abs(samples) ** 2

    average_power = float(np.mean(power))

    # RMS amplitude

    rms_amplitude = float(np.sqrt(average_power))

    # FFT
    fft_values = np.fft.fft(samples)

    fft_power = (np.abs(fft_values) ** 2)

    frequencies = np.fft.fftfreq(num_samples, d=1.0 / sample_rate)

    
    # Use positive frequencies only
    positive_mask = frequencies >= 0

    positive_frequencies = frequencies[positive_mask]

    positive_power = fft_power[positive_mask]

    if len(positive_power) == 0:

        return {
            "average_power": average_power,
            "rms_amplitude": rms_amplitude,
        }

    # Dominant frequency
    peak_index = int(np.argmax(positive_power))

    peak_frequency = float(positive_frequencies[peak_index])

    peak_power = float(positive_power[peak_index])

    # Frequency resolution
    frequency_resolution = float(sample_rate / num_samples)

    # Frequency error
    frequency_error = abs(peak_frequency - expected_frequency)

    # Expected-frequency bin
    expected_index = int(np.argmin(np.abs(positive_frequencies - expected_frequency)))

    expected_power = float(positive_power[expected_index])

    # Power ratio
    total_fft_power = float(
        np.sum(positive_power)
    )

    if total_fft_power > 0:

        tone_power_ratio = (expected_power / total_fft_power)

    else:

        tone_power_ratio = 0.0


    # Convert power ratio to dB

    if tone_power_ratio > 0:

        tone_power_db = float(10 * np.log10(tone_power_ratio))

    else:

        tone_power_db = -np.inf

    return {
        "average_power": average_power,
        "rms_amplitude": rms_amplitude,
        "peak_frequency": peak_frequency,
        "expected_frequency": float(expected_frequency),
        "frequency_error": float(frequency_error),
        "frequency_resolution": frequency_resolution,
        "peak_power": peak_power,
        "expected_frequency_power": expected_power,
        "tone_power_ratio": float(tone_power_ratio),
        "tone_power_db": tone_power_db,
    }


def main():

    # ==================================================
    # Directory structure
    #
    # experiment/
    #
    # ├── parameters.json
    # ├── rx.iq
    # ├── results.json
    # ├── analysis.py
    # ├── node_rx/
    # │   └── rx_chain.py
    # └── node_tx/
    #     └── tx_chain.py
    #
    # ==================================================

    script_dir = os.path.dirname(os.path.abspath(__file__))

    experiment_dir = os.path.abspath(os.path.join(script_dir, "..",))

    IQ_FILE = os.path.join(experiment_dir, "rx.iq",)

    PARAM_FILE = os.path.join(experiment_dir, "parameters.json",)

    RESULT_FILE = os.path.join(experiment_dir, "results.json",)

    # Load parameters

    params = load_parameters(PARAM_FILE)

    sample_rate = float(params.get("sample_rate", 1_000_000))

    expected_frequency = float(params.get("tone_frequency", 0))

    expected_samples = int(params.get("capture_samples", 0))

    # Initial result

    result = {
        "status": "failed",
        "reason": "",
        "metrics": {
            "sample_rate": sample_rate,
            "expected_frequency": expected_frequency,
            "expected_samples": expected_samples,
        },
    }

    # Check RX file
    if not os.path.exists(IQ_FILE):

        result["reason"] = ("rx.iq not found")

    else:

        # Read IQ samples

        try:

            samples = np.fromfile(IQ_FILE, dtype=np.complex64)

        except Exception as error:

            result["reason"] = (f"Failed to read rx.iq: {error}")

            samples = None

        if samples is not None:

            num_samples = len(samples)

            result["metrics"]["samples_received"] = int(num_samples)

            # Check sample count

            if num_samples == 0:

                result["reason"] = ("No samples received")

            else:

                # Basic sample validation
                if not np.all(np.isfinite(samples.real)) or not np.all(np.isfinite(samples.imag)):

                    result["reason"] = ("Invalid IQ samples detected")

                else:

                    # Perform signal analysis

                    analysis = calculate_analysis(samples, sample_rate, expected_frequency)

                    result["metrics"].update(analysis)


                    # Sample count check

                    if expected_samples > 0:

                        sample_count_ok = (num_samples >= expected_samples)

                    else:

                        sample_count_ok = (num_samples > 0)

                    result["metrics"]["sample_count_ok"] = sample_count_ok


                    # Frequency tolerance
                    tolerance = max(
                        analysis["frequency_resolution"], sample_rate / 1000.0)

                    frequency_ok = (
                        analysis["frequency_error"] <= tolerance)

                    result["metrics"]["frequency_tolerance"] = float(tolerance)

                    result["metrics"]["frequency_ok"] = frequency_ok


                    # Signal power check
                
                    power_ok = (
                        analysis["average_power"] > 1e-12)

                    result["metrics"]["power_ok"] = power_ok


                    # Final PASS / FAIL
            
                    if (sample_count_ok and frequency_ok and power_ok):

                        result["status"] = ("passed")

                        result["reason"] = ("Expected signal detected successfully")

                    else:

                        reasons = []

                        if not sample_count_ok:

                            reasons.append("insufficient samples")

                        if not frequency_ok:

                            reasons.append("expected tone frequency not detected")

                        if not power_ok:

                            reasons.append("received signal power too low")

                        result["reason"] = ("; ".join(reasons))


    # Save results.json
    with open(RESULT_FILE, "w", encoding="utf-8") as f:

        json.dump(result, f, indent=4)

    # Print result for execution controller

    print("::RESULT::" + json.dumps(result))


if __name__ == "__main__":
    main()