#!/usr/bin/env python3

import argparse
import subprocess
import time

from server import app

parser = argparse.ArgumentParser(description='Helper Script to run server and client')
parser.add_argument('--client-path', type=str, help='Path to ic20 client', default='ic20_linux')
parser.add_argument('--seed', type=str, help='A custom seed to replace the randomly generated one', default=str(int(time.time())))

args = parser.parse_args()

print(f'Seed: {args.seed}')

with subprocess.Popen(['python', 'server.py', '--seed', args.seed]) as proc:
    time.sleep(2)
    client = subprocess.Popen([args.client_path, '-u', 'http://localhost:5000/', '-s', args.seed], stdout=subprocess.DEVNULL)
    client.wait()
    proc.terminate()
