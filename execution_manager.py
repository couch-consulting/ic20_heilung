#!/usr/bin/env python3

import argparse
import subprocess
import time

from server import app

parser = argparse.ArgumentParser(description='Helper Script to run server and client')
parser.add_argument('--client-path', type=str, help='Path to ic20 client', default='ic20_linux')
parser.add_argument('--seed', type=str, help='A custom seed to replace the randomly generated one')
parser.add_argument('--short', help='Print only a view game details', action='store_true')
parser.add_argument('--silent', help='Remove any output of the game', action='store_true')

parser.add_argument('--test', type=int, help='Starts a test run for the specified number of epochs', default=20)

args = parser.parse_args()

# if args.test:


# Set seed default
args.seed = str(int(time.time()))

print(f'Seed: {args.seed}')
subprocess_cmd = ['python', 'server.py', '--seed', args.seed]
if args.short:
    # Check for silent
    subprocess_cmd.append('--short')
if args.silent:
    # Check for silent
    subprocess_cmd.append('--silent')

with subprocess.Popen(subprocess_cmd) as proc:
    time.sleep(2)
    client = subprocess.Popen([args.client_path, '-u', 'http://localhost:5000/', '-s', args.seed], stdout=subprocess.DEVNULL)
    client.wait()
    proc.terminate()

# TODO get results here avg round + win/loss
