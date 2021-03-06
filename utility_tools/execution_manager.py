#!/usr/bin/env python3

import argparse
import os.path
import subprocess
import time

import requests

BASEPATH = os.path.dirname(os.path.dirname(__file__))

parser = argparse.ArgumentParser(
    description='Helper Script to run server and client')
parser.add_argument('--client-path', type=str,
                    help='Path to ic20 client', default='ic20_linux')
parser.add_argument('--seed', type=str, help='A custom seed to replace the randomly generated one',
                    default=str(int(time.time())))
parser.add_argument(
    '--silent', help='Remove any output of the server', action='store_true')
parser.add_argument('--port', type=str, help='Port for server', default='5000')
parser.add_argument('--no_obs', help='Disable Observer', action='store_true')
parser.add_argument('--epochs', type=int,
                    help='Starts a test run for the specified number of epochs', default=1)

args = parser.parse_args()
seed = args.seed

base_url = 'http://localhost:' + args.port

# Parse args and build flask startup
subprocess_cmd = ['python', BASEPATH + '/server.py',
                  '--seed', seed, '--port', args.port]
if args.silent:
    subprocess_cmd.append('--silent')
if args.no_obs:
    subprocess_cmd.append('--no_obs')


# Msr time
start = time.time()
# Start execution
with subprocess.Popen(subprocess_cmd) as proc:
    # Wait for flask to spin up
    time.sleep(2)

    # Tmp vars
    avg_rounds_loss = 0
    avg_rounds_win = 0
    won_games = 0

    # Loop in case of test
    for i in range(args.epochs):
        # Remove observer.json before run, because the observer would just append otherwise.
        observer_path = f'{BASEPATH}/observations/observer-{seed}.json'
        if os.path.isfile(observer_path):
            os.remove(observer_path)
        # Play game
        client = subprocess.Popen([args.client_path, '-u', base_url + '/', '-s', seed],
                                  stdout=subprocess.DEVNULL)
        client.wait()

        # Collect result
        results = requests.get(base_url + '/last_state').json()
        if results['outcome'] == 'win':
            won_games += 1
            avg_rounds_win += results['rounds']
        else:
            avg_rounds_loss += results['rounds']
        print(
            f'Epoch: {i} | Seed: {seed} | Outcome: {results["outcome"]} | Rounds: {results["rounds"]}')

        # Update Seed for next iteration
        # +i*1000 for death rounds with two Admiral Trips spawnings
        # Just add a large number to avoid collisions
        seed = str(int(time.time()) + i * 1000)
        requests.post(base_url + '/seed/' + seed)

    # Print final results
    if args.epochs > 1:
        avg_rounds_loss = avg_rounds_loss / max((args.epochs - won_games), 1)
        avg_rounds_win = avg_rounds_win / won_games
        win_ratio = won_games / args.epochs
        print(
            f'Win %: {win_ratio}| Avg. Won Rounds: {avg_rounds_win} | Avg. Loss Rounds: {avg_rounds_loss} | Epochs: {args.epochs}')

    # Close
    proc.terminate()

end = time.time()
print(f'Overall time: {end - start}')
