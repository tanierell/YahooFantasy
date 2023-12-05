import os
import time
import pytz
import pickle
import requests
import datetime
import numpy as np
import pandas as pd
import concurrent.futures
import matplotlib.pyplot as plt
from collections import defaultdict

from NBA_fantasy.yahoo.utils import fetch_daily_data, fetch_teams_roster_ids, init_configuration


def best_FA_pickup(sc, lg, league_id, plot=False, current_week=None, league_name=""):
    current_week = lg.current_week() if current_week is None else current_week
    start_date, end_date = lg.week_date_range(current_week)
    start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time()) + datetime.timedelta(hours=2)

    final_trans_dict = {'add': {}, 'drop': {}}
    for specific_type in ['add', 'drop']:
        transactions = lg.transactions(tran_types=specific_type, count='')
        dest_or_source = 'destination_team_name' if specific_type == 'add' else 'source_team_name'
        for i, transaction in enumerate([x for x in transactions if isinstance(x, dict)]):
            transaction_type = transaction['type']
            transaction_id = transaction['transaction_id']
            transaction_date = datetime.datetime.fromtimestamp(int(transaction['timestamp']))
            if transaction_date < start_date:
                continue

            if transaction_type == "add/drop":
                if specific_type == 'add':
                    add_drop_flag = '0'
                else:
                    add_drop_flag = '1'
            elif specific_type == transaction_type:
                add_drop_flag = '0'
            else:
                continue

            fetched_transaction = transaction['players'][add_drop_flag]['player']
            player_name = fetched_transaction[0][2]['name']['full']
            player_id = fetched_transaction[0][1]['player_id']

            try:
                manager = fetched_transaction[1]['transaction_data'][dest_or_source]
            except:
                manager = fetched_transaction[1]['transaction_data'][0][dest_or_source]

            final_trans_dict[specific_type][transaction_id] = {'player_name': player_name, 'player_id': player_id,
                                                               'date': transaction_date,
                                                               'manager': manager}

    added_players_df = pd.DataFrame.from_dict(final_trans_dict['add'], orient='index')
    dropped_players_df = pd.DataFrame.from_dict(final_trans_dict['drop'], orient='index')

    added_players_ids = list(added_players_df['player_id'].unique())
    dropped_players_ids = list(dropped_players_df['player_id'].unique())

    week_dates = [start_date + datetime.timedelta(days=i) for i in range(7)]
    added_players_weekly_stats = {date.strftime('%d-%m-%Y'): fetch_daily_data(sc, added_players_ids, date=date) for date in week_dates}
    dropped_players_weekly_stats = {date.strftime('%d-%m-%Y'): fetch_daily_data(sc, dropped_players_ids, date=date) for date in week_dates}

    added_players_df['transaction_type'] = 'add'
    # dropped_players_df['transaction_type'] = 'drop'
    # transactions_df = pd.concat([added_players_df, dropped_players_df], axis=0)

    ids_names_statutes_by_date = {date.strftime('%d-%m-%Y'): fetch_teams_roster_ids(sc, lg, datetime_obj=date, league_id=league_id)
                                  for date in week_dates}

    weekly_transactions_stats_by_manager = {manager: defaultdict(list) for manager in added_players_df['manager'].unique()}
    for (manager, player_id), manager_df in added_players_df.groupby(['manager', 'player_id']):
        for date, ids_names_statutes in ids_names_statutes_by_date.items():
            daily_manager_roster = ids_names_statutes[manager]['ids']
            if int(player_id) in daily_manager_roster:
                weekly_transactions_stats_by_manager[manager][int(player_id)].append(date)

    stat_cols = ['PTS', 'FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'REB', 'AST', 'ST', 'BLK', 'TO', 'player_id']
    weekly_manager_temp = {manager: None for manager in weekly_transactions_stats_by_manager}
    for manager in weekly_transactions_stats_by_manager:
        team_weekly_df = pd.DataFrame(columns=stat_cols)
        for player_id, dates_list in weekly_transactions_stats_by_manager[manager].items():
            player_weekly = np.zeros(shape=(1, len(stat_cols)))
            player_name = ''
            for date in dates_list:
                daily_df = added_players_weekly_stats[date]
                daily_df.replace('-', 0, inplace=True)
                temp = daily_df[daily_df['player_id'] == str(player_id)][stat_cols].values.astype(int)
                player_weekly += np.array(temp)

                if len(daily_df) > 0:
                    player_name = daily_df[daily_df['player_id'] == str(player_id)].index[0]

            team_weekly_df.loc[player_name] = player_weekly[0]

        team_weekly_df.drop('player_id', axis=1, inplace=True)
        weekly_manager_temp[manager] = team_weekly_df

    final_df = []
    for team, df in weekly_manager_temp.items():
        reformatted_df = df.copy()
        reformatted_df['FG%'] = reformatted_df['FGM'] / reformatted_df['FGA']
        reformatted_df['FT%'] = reformatted_df['FTM'] / reformatted_df['FTA']
        reformatted_df.drop(['FGM', 'FGA', 'FTM', 'FTA'], axis=1, inplace=True)
        reformatted_df['manager'] = team
        final_df.append(reformatted_df)

    final_df = pd.concat(final_df)
    final_df.fillna(0, inplace=True)

    copied_final_df = final_df.copy()
    final_df.drop('manager', axis=1, inplace=True)
    column_percentages = final_df.divide(final_df.sum(axis=0), axis=1)
    column_percentages['TO'] *= -1
    weighted_avg_impact = column_percentages.mean(axis=1)
    filtered_players = weighted_avg_impact.sort_values(ascending=False)[:20]
    filtered_players = filtered_players[filtered_players >= 0.01]

    top_k_players = filtered_players.index[:3]
    top_k_stats = final_df.loc[top_k_players]

    textual_summary_title = f"Best FA Pickups - Week {current_week}\n"
    i = 1
    for name, values in top_k_stats.iterrows():
        values = values.round(2)
        manager = copied_final_df.loc[name]['manager']
        str_values = ", ".join([f"{col} - {value}" for col, value in values.items()])
        textual_summary_title += f"\n\t{i}. {name} - {manager} \n\t\t{str_values}\n"
        i += 1

    if not os.path.exists(f'outputs/Texts/{league_name}/{current_week}'):
        os.makedirs(f'outputs/Texts/{league_name}/{current_week}')

    with open(f'outputs/Texts/{league_name}/{current_week}/weekly_best_FA.txt', 'w', encoding='utf-8') as f:
        f.write(textual_summary_title)

    plt.figure(figsize=(8, 8))
    plt.pie(filtered_players, labels=filtered_players.index, autopct='%1.1f%%', startangle=140)

    plt.axis('equal')
    if not os.path.exists(f'outputs/Plots/{league_name}/{current_week}'):
        os.makedirs(f'outputs/Plots/{league_name}/{current_week}')
    plt.savefig(f'outputs/Plots/{league_name}/{current_week}/weekly_best_pickup_pie.png', bbox_inches='tight')  # Replace 'pie_chart.png' with your desired file name and format
    if plot:
        plt.show()


def get_weekly_FA_projection(sc, lg, league_id, end_date, path_to_db='../local_db'):
    kwargs = {'params': {'format': 'json'}, 'allow_redirects': True}
    top_fa_names = []
    top_fa_status = []
    top_k = 100
    with sc.session as s:
        for start in range(0, top_k, 25):
            url = f'https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/players;status=A;sort=AR;start={start}'
            res = s.request('GET', url, **kwargs).json()['fantasy_content']['league'][1]['players']
            top_fa_names += [fa_obj['player'][0][2]['name']['full'] for i, fa_obj in res.items() if i != 'count']
            for i, fa_obj in res.items():
                if i != 'count':
                    status = '' if 'status' not in fa_obj['player'][0][4] else fa_obj['player'][0][4]['status']
                    top_fa_status.append(status)
    s.close()

    full_players_avg = pickle.load(open(f"{path_to_db}/players_averages/players_avg_df.pkl", 'rb'))
    ect_time = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
    today_date = datetime.datetime.combine(ect_time, datetime.time())
    full_players_schedule = pickle.load(open(f"{path_to_db}/schedule/full_players_schedule.pkl", 'rb'))
    fetched_dates = ((full_players_schedule.columns <= pd.to_datetime(end_date, format='%Y-%m-%d')) &
                     (full_players_schedule.columns >= pd.to_datetime(today_date, format='%Y-%m-%d')))
    fetched_players_schedule = full_players_schedule.loc[:, fetched_dates]
    fetched_players_schedule.loc[:, ['number_of_games']] = fetched_players_schedule.sum(axis=1)
    for name in top_fa_names:
        if name not in full_players_avg.index:
            print(f"{name} not in full_players_avg.index")

    stats_cols = ['FGM', 'FGA', 'FTM', 'FTA', 'FG3M', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    fa_averages = full_players_avg[full_players_avg.index.isin(top_fa_names)]
    fa_averages.loc[:, ['status']] = fa_averages.index.map(dict(zip(top_fa_names, top_fa_status)))
    fa_averages = fa_averages.merge(fetched_players_schedule, left_index=True, right_index=True)
    fa_averages = fa_averages[fa_averages['status'] != 'INJ']
    num_games_vector = fa_averages.loc[:, ['number_of_games']].values
    current_team_averages = fa_averages[stats_cols]
    fa_projections = current_team_averages.mul(num_games_vector, axis=0)
    fa_projections.rename(columns={'TOV': 'TO', 'FG3M': '3PTM', 'STL': 'ST'}, inplace=True)
    fa_projections = fa_projections[['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']]
    fa_projections.fillna(0, inplace=True)
    fa_projections = fa_projections[~(fa_projections == 0).all(axis=1)]

    return fa_projections


if __name__ == '__main__':
    # league_name = "Ootan"
    league_name = "Sheniuk"
    all_time_players_list = pickle.load(open('../local_db/all_time_players_nba_api.pkl', 'rb'))
    sc, lg, league_id, current_week, start_date, end_date = init_configuration(league_name=league_name, week=6, from_file="../oauth2.json")
    fa_projections = get_weekly_FA_projection(sc, lg, league_id, end_date)
    print(fa_projections)