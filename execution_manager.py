#!/usr/bin/env python3

import argparse
import subprocess
import time
import requests

from server import app

parser = argparse.ArgumentParser(description='Helper Script to run server and client')
parser.add_argument('--client-path', type=str, help='Path to ic20 client', default='ic20_linux')
parser.add_argument('--seed', type=str, help='A custom seed to replace the randomly generated one',
                    default=str(int(time.time())))
parser.add_argument('--silent', help='Remove any output of the server', action='store_true')
parser.add_argument('--test', type=int, help='Starts a test run for the specified number of epochs')
parser.add_argument('--port', type=str, help='Port for server', default='5000')
args = parser.parse_args()

# Set seed default

# Parse args
subprocess_cmd = ['python', 'server.py', '--seed', args.seed, '--port', args.port]
if args.silent:
    subprocess_cmd.append('--silent')
iterations = 1
if args.test:
    iterations = args.test

# Msr time
start = time.time()
# Start execution
with subprocess.Popen(subprocess_cmd) as proc:
    time.sleep(2)

    # Tmp vars
    avg_rounds = 0
    won_games = 0

    # Loop in case of test
    for i in range(iterations):
        # Play game
        client = subprocess.Popen([args.client_path, '-u', 'http://localhost:' + args.port + '/', '-s', args.seed],
                                  stdout=subprocess.DEVNULL)
        client.wait()

        # Collect result
        results = requests.get('http://localhost:' + args.port + '/last_state').json()
        avg_rounds += results['rounds']
        if results['outcome'] == 'win':
            won_games += 1
        print(f'Iter#: {i} | Seed: {args.seed} | Outcome: {results["outcome"]} | Rounds: {results["rounds"]}')

        # Update Seed for next iteration
        args.seed = str(int(time.time()))
        requests.post('http://localhost:' + args.port + '/seed/' + args.seed)

    # Print final results
    if iterations > 1:
        avg_rounds = avg_rounds / iterations
        win_ratio = won_games / iterations
        print(f'Win %: {win_ratio} | Avg. Rounds: {avg_rounds}')

    # Close
    proc.terminate()

end = time.time()
print(f'Overall time: {end - start}')
