import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm, lognorm
import os
import numpy as np
import pytz
import datetime
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa


def convert_id_to_cat(stat_id):
    """Convert stat id to category. Returns category name. expects stat_id to be string."""
    stat_id_to_category = {3: 'FGA', 4: 'FGM', 5: 'FG%', 6: 'FTA', 7: 'FTM', 8: 'FT%', 10: '3PTM', 12: 'PTS',
                           15: 'REB', 16: 'AST', 17: 'ST', 18: 'BLK', 19: 'TO', 9004003: 'FGM/FGA', 9007006: 'FTM/FTA'}

    return stat_id_to_category.get(int(stat_id), None)


def prob_greater_than_value(df, col_name, value):
    col = df[col_name]
    col_mean = col.mean()
    col_std = col.std()

    # z_score = (value - col_mean) / col_std
    #     # prob = 1 - norm.cdf(z_score)
    prob = 1 - norm.cdf(value, loc=col_mean, scale=col_std)

    return prob


if __name__ == '__main__':
    players_avg = pickle.load(open('local_db/players_averages/players_avg_df.pkl', 'rb'))
    players_avg.drop(columns=['player_id'], inplace=True)
    matchups_diff = pickle.load(open('local_db/all_time_matchups_differential.pkl', 'rb'))
    df = matchups_diff.copy()
    player_a_stats = {'PTS': 7, 'BLK': 2, 'REB': 8, 'AST': 1}
    player_b_stats = {'PTS': 17, 'BLK': 0, 'REB': 3, 'AST': 5}
    '''multiply by 3 each stat to get total points for each stat'''''
    player_a_stats = {k: v * 3 for k, v in player_a_stats.items()}
    player_b_stats = {k: v * 3 for k, v in player_b_stats.items()}
    for value_to_check in [1, 5, 10, 50, 80, 100, 150, 200, 250, 400]:
        player_a_contributions = {}
        player_b_contributions = {}
        player_a_avg, player_b_avg = 0, 0
        for col_name in player_a_stats.keys():
            player_a_prob = prob_greater_than_value(df, col_name, value_to_check)
            player_b_prob = prob_greater_than_value(df, col_name, value_to_check)

            player_a_contributions[col_name] = player_a_stats[col_name] * player_a_prob
            player_b_contributions[col_name] = player_b_stats[col_name] * player_b_prob

            player_a_avg += player_a_contributions[col_name]
            player_b_avg += player_b_contributions[col_name]

            print(f"{col_name} differential: {value_to_check}:")
            print(f"\tPlayer A contribution: {player_a_contributions[col_name]}")
            print(f"\tPlayer B contribution: {player_b_contributions[col_name]}")

        print(f"Player A average: {player_a_avg / len(player_b_stats)}, Player B average: {player_b_avg / len(player_b_stats)}")
        print("- - -" * 5)

    print(1/0)
    # df = players_avg.copy()
    # players_avg.loc['avg'] = players_avg.mean(axis=0)
    # players_avg.loc['std'] = players_avg.std(axis=0)
    n_rows, n_cols = 3, 4
    fig, axes = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(16, 12))
    axes = axes.flatten()

    # Plotting histograms for each column
    for i, column in enumerate(df.columns):
        axes[i].hist(df[column], bins=10, edgecolor='black')
        axes[i].set_xlabel(column)
        axes[i].set_ylabel('Frequency')

    # Turn off any unused subplots
    for j in range(i + 1, n_rows * n_cols):
        axes[j].axis('off')

    plt.tight_layout()
    plt.savefig('testing.png')
    plt.show()
