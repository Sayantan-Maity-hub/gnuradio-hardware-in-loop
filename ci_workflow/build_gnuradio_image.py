#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build a GNU Radio Docker image from an exact Git commit SHA.

The generated image uses the official CortexLab GNU Radio image
as its base and builds GNU Radio from the requested PR SHA.
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import config

default_base_image = config.DEFAULT_BASE_IMAGE


def run_command(command, cwd=None):
    """Run a command and stop if it fails."""

    subprocess.run(command, cwd=cwd, check=True)


def validate_sha(sha):
    """Basic validation of a Git SHA."""

    if not sha:
        raise ValueError("GNU Radio SHA is required.")

    # Accept full SHA and abbreviated SHA.
    if not all(c in "0123456789abcdefABCDEF" for c in sha):

        raise ValueError(f"Invalid Git SHA: {sha}")

    if len(sha) < 7:

        raise ValueError(
            "GNU Radio SHA must contain at least 7 hexadecimal characters."
        )


def create_dockerfile(path, base_image, sha):
    """
    Create a Dockerfile that builds GNU Radio from the requested SHA.
    """

    dockerfile = f"""
FROM {base_image}

ARG GNU_RADIO_SHA={sha}

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies.
# The CortexLab base image should already contain most of the
# GNU Radio runtime dependencies.
RUN apt-get update && apt-get install -y \\
    git \\
    cmake \\
    ninja-build \\
    build-essential \\
    pkg-config \\
    python3-dev \\
    python3-pip \\
    libboost-all-dev \\
    libfftw3-dev \\
    libgsl-dev \\
    libcppunit-dev \\
    libgmp-dev \\
    libmpfr-dev \\
    libcodec2-dev \\
    libcppunit-dev \\
    liblog4cpp5-dev \\
    libsndfile1-dev \\
    libusb-1.0-0-dev \\
    libuhd-dev \\
    uhd-host \\
    && rm -rf /var/lib/apt/lists/*

# Clone GNU Radio source.
RUN git clone https://github.com/gnuradio/gnuradio.git /opt/gnuradio

# Checkout the exact PR SHA.
RUN cd /opt/gnuradio && \\
    git checkout ${{GNU_RADIO_SHA}} && \\
    git submodule update --init --recursive

# Configure GNU Radio.
RUN mkdir -p /opt/gnuradio/build && \\
    cd /opt/gnuradio/build && \\
    cmake .. \\
        -G Ninja \\
        -DCMAKE_BUILD_TYPE=Release \\
        -DCMAKE_INSTALL_PREFIX=/usr/local \\
        -DENABLE_DEFAULT=OFF \\
        -DENABLE_GNURADIO_RUNTIME=ON \\
        -DENABLE_GR_ANALOG=ON \\
        -DENABLE_GR_BLOCKS=ON \\
        -DENABLE_GR_DIGITAL=ON \\
        -DENABLE_GR_FFT=ON \\
        -DENABLE_GR_FILTER=ON \\
        -DENABLE_GR_PDU=ON \\
        -DENABLE_GR_UHD=ON \\
        -DENABLE_GR_FEC=ON

# Build GNU Radio.
RUN cd /opt/gnuradio/build && \\
    ninja -j$(nproc)

# Install GNU Radio.
RUN cd /opt/gnuradio/build && \\
    ninja install

# Refresh dynamic linker cache.
RUN ldconfig

# Make sure Python can find the newly installed GNU Radio.
ENV PYTHONPATH="/usr/local/lib/python3/dist-packages:/usr/local/lib/python3/site-packages:$PYTHONPATH"

# Keep CortexLab SSH behavior.
EXPOSE 2222

CMD ["/usr/sbin/sshd", "-p", "2222", "-D"]
"""

    path.write_text(dockerfile.strip() + "\n")

    print(f"Created Dockerfile: {path}")


def build_image(dockerfile, image, sha):
    """Build the Docker image."""

    run_command(
        [
            "docker",
            "build",
            "--build-arg",
            f"GNU_RADIO_SHA={sha}",
            "-f",
            str(dockerfile),
            "-t",
            image,
            ".",
        ]
    )


def verify_image(image):
    """Verify that the generated image contains GNU Radio."""

    print("Verifying generated image...")

    run_command(
        [
            "docker",
            "run",
            "--rm",
            image,
            "python3",
            "-c",
            (
                "import gnuradio; "
                "print('GNU Radio Python module:', gnuradio.__file__)"
            ),
        ]
    )

    print("GNU Radio import test passed.")


def push_image(image):
    """Push the image to the configured registry."""

    print(f"Pushing image: {image}")

    run_command(
        [
            "docker",
            "push",
            image,
        ]
    )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Build a CortexLab-compatible GNU Radio Docker image "
            "from an exact Git SHA."
        )
    )

    parser.add_argument(
        "--sha",
        default=os.getenv("GNU_RADIO_SHA"),
        help="GNU Radio Git commit SHA.",
    )

    parser.add_argument(
        "--base-image",
        default=os.getenv(
            "CORTEXLAB_BASE_IMAGE",
            default_base_image,
        ),
        help=("CortexLab base Docker image. " "Default: %(default)s"),
    )

    parser.add_argument(
        "--image",
        default=os.getenv("GNU_RADIO_IMAGE"),
        help=(
            "Full Docker image name/tag to create. "
            "Example: ghcr.io/my-org/gnuradio-hil:abc123"
        ),
    )

    parser.add_argument(
        "--push",
        action="store_true",
        help="Push the generated image to the registry.",
    )

    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the post-build GNU Radio import test.",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    try:
        validate_sha(args.sha)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not args.image:

        print(
            "ERROR: Docker image name is required. Use --image or GNU_RADIO_IMAGE.",
            file=sys.stder,
        )
        return 1

    with tempfile.TemporaryDirectory(prefix="gnuradio-hil-build-") as temp_dir:

        build_dir = Path(temp_dir)

        dockerfile = build_dir / "Dockerfile"

        create_dockerfile(
            dockerfile=dockerfile,
            base_image=args.base_image,
            sha=args.sha,
        )

        build_image(
            dockerfile=dockerfile,
            image=args.image,
            sha=args.sha,
        )

    if not args.no_verify:
        verify_image(args.image)

    if args.push:
        push_image(args.image)

    print(f"Image: {args.image}")
    print(f"GNU Radio SHA: {args.sha}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
