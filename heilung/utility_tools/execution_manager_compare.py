#!/usr/bin/env python3

import argparse
import os.path
import subprocess
import time

import requests

from server import app


def client(won_games, avg_rounds_win, avg_rounds_loss, base_url, seed, version='human'):
    requests.post(base_url + '/seed/' + seed)
    # Remove observer.json before run, because the observer would just append otherwise.
    observer_path = f'../../observations/observer-{seed}.json'
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
    print(f'[{version}] Epoch: {i} | Seed: {seed} | Outcome: {results["outcome"]} | Rounds: {results["rounds"]}')

    return won_games, avg_rounds_win, avg_rounds_loss, results['rounds'], results['outcome']


parser = argparse.ArgumentParser(description='Helper Script to run server and client')
parser.add_argument('--client-path', type=str, help='Path to ic20 client', default='ic20_linux')
parser.add_argument('--seed', type=str, help='A custom seed to replace the randomly generated one',
                    default=str(int(time.time())))
parser.add_argument('--silent', help='Remove any output of the server', action='store_true')
parser.add_argument('--port', type=str, help='Port for server', default='5000')
parser.add_argument('--no_obs', help='Disable Observer', action='store_true')
parser.add_argument('--epochs', type=int, help='Starts a test run for the specified number of epochs', default=1)
parser.add_argument('--compare', type=tuple, help='Heuristics to compare', default=(('Human', '2'), ('Ensemble', '0')))

args = parser.parse_args()
seed = args.seed
heuristic_1 = args.compare[0]
heuristic_2 = args.compare[1]

# Parse args and build flask startup
subprocess_cmd_1 = ['python', '../../server.py', '--seed', seed, '--port', args.port, '--h', heuristic_1[1]]
if args.silent:
    subprocess_cmd_1.append('--silent')
if args.no_obs:
    subprocess_cmd_1.append('--no_obs')
base_url_1 = 'http://localhost:' + args.port
version_1 = heuristic_1[0]

subprocess_cmd_2 = ['python', '../../server.py', '--seed', seed, '--port', str(int(args.port) + 1000), '--h',
                    heuristic_2[1]]
if args.silent:
    subprocess_cmd_2.append('--silent')
if args.no_obs:
    subprocess_cmd_2.append('--no_obs')
base_url_2 = 'http://localhost:' + str(int(args.port) + 1000)
version_2 = heuristic_2[0]

# Counter vars
start = time.time()
score_1 = 0
score_2 = 0

# Start execution
with subprocess.Popen(subprocess_cmd_1) as proc1:
    with subprocess.Popen(subprocess_cmd_2) as proc2:
        # Wait for flask to spin up
        time.sleep(2)

        # Tmp vars
        avg_rounds_loss_1 = 0
        avg_rounds_win_1 = 0
        won_games_1 = 0

        avg_rounds_loss_2 = 0
        avg_rounds_win_2 = 0
        won_games_2 = 0

        # Loop in case of test
        for i in range(args.epochs):
            # Update Seed for next iteration
            # +i*1000 for death rounds with two Admiral Trips spawnings
            # Just add a large number to avoid collisions
            seed = str(int(time.time()) + i * (1000))
            won_games_1, avg_rounds_win_1, avg_rounds_loss_1, rounds_1, outcome_1 = client(won_games_1,
                                                                                           avg_rounds_win_1,
                                                                                           avg_rounds_loss_1,
                                                                                           base_url_1,
                                                                                           seed,
                                                                                           version=version_1)
            won_games_2, avg_rounds_win_2, avg_rounds_loss_2, rounds_2, outcome_2 = client(won_games_2,
                                                                                           avg_rounds_win_2,
                                                                                           avg_rounds_loss_2,
                                                                                           base_url_2,
                                                                                           seed,
                                                                                           version=version_2)
            if outcome_1 == 'win' and outcome_2 != 'win':
                score_1 += 1
            elif outcome_1 != 'win' and outcome_2 == 'win':
                score_2 += 1
            elif outcome_1 == 'win' and outcome_2 == 'win':
                if rounds_1 < rounds_2:
                    score_1 += 1
                elif rounds_1 > rounds_2:
                    score_2 += 1
                else:
                    #  no one gets points, no it can be interpreted as just the difference value of the methods
                    pass

            else:
                # Both did lose
                if rounds_1 > rounds_2:
                    score_1 += 1
                elif rounds_1 < rounds_2:
                    score_2 += 1
                else:
                    # no one gets points
                    pass

        # Print final results
        if args.epochs > 1:
            avg_rounds_loss = avg_rounds_loss_1 / max((args.epochs - won_games_1), 1)
            avg_rounds_win = avg_rounds_win_1 / won_games_1
            win_ratio = won_games_1 / args.epochs
            print(
                f'[1]: Win %: {win_ratio}| Avg. Won Rounds: {avg_rounds_win} | Avg. Loss Rounds: {avg_rounds_loss} | Epochs: {args.epochs}')
            print(f'Score of {version_1} heuristic is {score_1}')
            avg_rounds_loss = avg_rounds_loss_2 / max((args.epochs - won_games_2), 1)
            avg_rounds_win = avg_rounds_win_2 / won_games_2
            win_ratio = won_games_2 / args.epochs
            print(
                f'[2]: Win %: {win_ratio}| Avg. Won Rounds: {avg_rounds_win} | Avg. Loss Rounds: {avg_rounds_loss} | Epochs: {args.epochs}')
            print(f'Score of {version_2} heuristic is {score_2}')

        # Close
        proc1.terminate()
        proc2.terminate()

end = time.time()
print(f'Overall time: {end - start}')
