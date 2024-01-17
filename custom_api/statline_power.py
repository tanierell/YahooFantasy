from utils import (init_db_config)

import warnings
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def plot_stats_dist(full_players_avg):
    df = full_players_avg[stats_cols]
    df = df.fillna(0)

    n_cols = 3
    n_rows = int(len(df.columns) / n_cols) + (len(df.columns) % n_cols > 0)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4, n_rows * 3))

    axes = axes.flatten()

    for i, col in enumerate(df.columns):
        sns.histplot(df[col], kde=True, ax=axes[i])
        mean, std = df[col].mean(), df[col].std()
        axes[i].set_title(f'{col} (mean: {mean:.2f}, std: {std:.2f})')

    for ax in axes:
        ax.set_xlabel('')
        ax.set_ylabel('')

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4)
    plt.show()


if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    engine = init_db_config(path_to_db_config='../config.ini')
    players_totals_query = f"SELECT * FROM players_season_totals;"
    full_players_totals = pd.read_sql_query(players_totals_query, engine, index_col='yahoo_id')

    stats_cols = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
    numeric_cols = [col for col in full_players_totals.columns if col not in ['full_name', 'status', 'team']]
    full_players_totals[numeric_cols] = full_players_totals[numeric_cols].apply(pd.to_numeric, errors='coerce')
    full_players_totals[stats_cols] = full_players_totals[stats_cols].div(full_players_totals['GP'], axis=0)
    full_players_avg = full_players_totals[['full_name', 'GP'] + stats_cols]
    full_players_avg['FGP'] = full_players_avg['FGM'] ** 2 / full_players_avg['FGA']
    full_players_avg['FTP'] = full_players_avg['FTM'] ** 2 / full_players_avg['FTA']
    full_players_avg.drop(columns=['FGM', 'FGA', 'FTM', 'FTA'], inplace=True)
    stats_cols = ['FGP', 'FTP', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
    full_players_avg = full_players_avg[full_players_avg['GP'] >= 10]

    df = full_players_avg.set_index('full_name')[stats_cols]
    df = df.fillna(0)
    mean_cat = df.mean(axis=0)
    std_cat = df.std(axis=0)
    df = (df - mean_cat) / std_cat
    df['TO'] *= -1
    punt_categories = ['PTS', 'REB', 'AST']
    df['total_value'] = df.sum(axis=1)
    df['punt_value'] = df[[col for col in stats_cols if col not in punt_categories]].sum(axis=1)
    df['dist_punt'] = df['total_value'] - df['punt_value']
    punt_df = df.sort_values(by='punt_value', ascending=False)
    df.sort_values(by='dist_punt', ascending=False, inplace=True)

    print(df)



