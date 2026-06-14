#!/usr/bin/env python3
"""Orchestrator: run c2ImageD11 tests across all Python versions via snakepit containers.

Usage: python3 tests/test_all.py

Uses Apptainer SIF containers from ../snakepit/ to test Python 2.7-3.14.
"""

from __future__ import print_function

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
SNAKEPIT_DIR = os.path.join(os.path.dirname(PROJECT_DIR), "snakepit")

PYTHON_VERSIONS = [
    ("2.7", "ubuntu20.04.sif"),
    ("3.8", "ubuntu20.04.sif"),
    ("3.9", "ubuntu24.04.sif"),
    ("3.10", "ubuntu24.04.sif"),
    ("3.11", "ubuntu24.04.sif"),
    ("3.12", "ubuntu24.04.sif"),
    ("3.13", "ubuntu24.04.sif"),
    ("3.14", "ubuntu24.04.sif"),
]

LOG_FILE = os.path.join(SCRIPT_DIR, "test_results.log")


def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")
    print(msg)


def run(version, sif_file):
    sif_path = os.path.join(SNAKEPIT_DIR, sif_file)
    if not os.path.exists(sif_path):
        log("SKIP {}/{}: SIF not found at {}".format(version, sif_file, sif_path))
        return False

    workspace = os.path.dirname(PROJECT_DIR)
    cmd = [
        "apptainer", "exec", "-e",
        "-B", workspace + ":/workspace",
        "--pwd", "/workspace/c2ImageD11/tests",
        sif_path,
        "/bin/bash", "run_multiversion.sh",
        "python" + version,
    ]

    log("RUN python{} via {} ...".format(version, sif_file))
    log("  cmd: " + " ".join(cmd))

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        log("  stdout: " + (proc.stdout[-200:] if proc.stdout else "(empty)"))

        if proc.returncode == 0:
            log("PASS python{}".format(version))
            return True
        else:
            log("FAIL python{} (rc={})".format(version, proc.returncode))
            if proc.stderr:
                log("  stderr: " + proc.stderr[-500:])
            return False
    except subprocess.TimeoutExpired:
        log("TIMEOUT python{}".format(version))
        return False
    except Exception as e:
        log("ERROR python{}: {}".format(version, e))
        return False


def main():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    log("=== c2ImageD11 multi-version test run ===")
    log("SIF directory: " + SNAKEPIT_DIR)
    log("Versions to test: " + ", ".join(v for v, _ in PYTHON_VERSIONS))
    log("")

    passed = 0
    failed = 0

    for version, sif_file in PYTHON_VERSIONS:
        ok = run(version, sif_file)
        if ok:
            passed += 1
        else:
            failed += 1
        log("")

    log("=== Summary: {} passed, {} failed ===".format(passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
