import os
import datetime
import logging
import pandas as pd
import matplotlib.pyplot as plt

from utils import init_configuration, run_yahoo_api_concurrently, init_db_config, fetch_roster_ids_by_dates


def best_FA_pickup(sc, engine, lg, league_id, plot=False, current_week=None, league_name=""):
    current_week = lg.current_week() if current_week is None else current_week
    start_date, end_date = lg.week_date_range(current_week)
    start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time()) + datetime.timedelta(hours=2)
    end_date = datetime.datetime.combine(end_date, datetime.datetime.min.time()) + datetime.timedelta(hours=19)

    final_trans_dict = {'add': {}, 'drop': {}}
    for specific_type in ['add', 'drop']:
        transactions = lg.transactions(tran_types=specific_type, count='')
        dest_or_source = 'destination_team_name' if specific_type == 'add' else 'source_team_name'
        for i, transaction in enumerate([x for x in transactions if isinstance(x, dict)]):
            transaction_type = transaction['type']
            transaction_id = transaction['transaction_id']
            transaction_date = datetime.datetime.fromtimestamp(int(transaction['timestamp']))
            if transaction_date < start_date or transaction_date > end_date:
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

    added_players_ids = tuple(added_players_df['player_id'].unique())
    added_players_df['transaction_type'] = 'add'
    dropped_players_df['transaction_type'] = 'drop'

    week_dates_objects = [start_date + datetime.timedelta(days=i) for i in range(7)]
    week_dates_query = tuple([date.strftime('%Y-%m-%d') for date in week_dates_objects])
    query = f"SELECT * FROM players_history_stats_daily WHERE yahoo_id IN {added_players_ids} AND date IN {week_dates_query}"
    added_players_weekly_stats = pd.read_sql_query(query, engine)

    rosters_data = fetch_roster_ids_by_dates(sc=sc, datetime_objects=week_dates_objects, league_id=league_id)
    rosters_data = rosters_data[['yahoo_id', 'date', 'team_name']]
    rosters_data['date'] = pd.to_datetime(rosters_data['date']).dt.date
    league_added_players_stats = added_players_weekly_stats.merge(rosters_data, on=['yahoo_id', 'date'], how='left')
    league_added_players_stats = league_added_players_stats[league_added_players_stats['team_name'].notnull()]
    numeric_cols = ['FGA','FGM', 'FTA', 'FTM', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
    added_players_sum = league_added_players_stats.groupby(['team_name', 'yahoo_id', 'full_name'])[numeric_cols].sum()
    added_players_sum.reset_index(inplace=True)
    added_players_sum['FG%'] = added_players_sum['FGM'] / added_players_sum['FGA']
    added_players_sum['FT%'] = added_players_sum['FTM'] / added_players_sum['FTA']
    added_players_sum = added_players_sum.fillna(0).drop(['FGM', 'FGA', 'FTM', 'FTA'], axis=1)

    numeric_cols = ['FG%', 'FT%', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
    added_players_sum = added_players_sum.set_index(['yahoo_id', 'full_name', 'team_name'])[numeric_cols]

    column_percentages = added_players_sum.divide(added_players_sum.sum(axis=0), axis=1)
    column_percentages['TO'] *= -1
    weighted_avg_impact = column_percentages.mean(axis=1)
    filtered_players = weighted_avg_impact.sort_values(ascending=False)[:20]
    filtered_players = filtered_players[filtered_players >= 0.01]

    top_k_players = filtered_players.index[:3]
    top_k_stats = added_players_sum.loc[top_k_players]

    textual_summary_title = f"Best FA Pickups - Week {current_week}\n"
    i = 1
    for id_name_manager, values in top_k_stats.iterrows():
        yahoo_id, player_name, manager = id_name_manager
        values = values.round(2)
        str_values = ", ".join([f"{col} - {value}" for col, value in values.items()])
        textual_summary_title += f"\n\t{i}. {player_name} - {manager} \n\t\t{str_values}\n"
        i += 1

    if not os.path.exists(f'../outputs/Texts/{league_name}/{current_week}'):
        os.makedirs(f'../outputs/Texts/{league_name}/{current_week}')

    with open(f'../outputs/Texts/{league_name}/{current_week}/weekly_best_FA.txt', 'w', encoding='utf-8') as f:
        f.write(textual_summary_title)

    plt.figure(figsize=(8, 8))
    plt.pie(filtered_players, labels=filtered_players.index, autopct='%1.1f%%', startangle=140)

    plt.axis('equal')
    if not os.path.exists(f'../outputs/Plots/{league_name}/{current_week}'):
        os.makedirs(f'../outputs/Plots/{league_name}/{current_week}')
    plt.savefig(f'../outputs/Plots/{league_name}/{current_week}/weekly_best_pickup_pie.png', bbox_inches='tight')  # Replace 'pie_chart.png' with your desired file name and format
    if plot:
        plt.show()


def get_weekly_FA_projection(sc, league_id, start_date, end_date, engine):
    urls = [f'https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/players;status=A;sort=AR;start={start}'
            for start in range(0, 200, 25)]

    responses = run_yahoo_api_concurrently(sc, urls)

    fetched_responses = [list(res['fantasy_content']['league'][1]['players'].values()) for res in responses]
    p_objects = [player['player'][0] for sublist in fetched_responses for player in sublist if isinstance(player, dict)]
    top_fa_names = [p_obj[2]['name']['full'] for p_obj in p_objects]
    top_fa_ids = [str(p_obj[1]['player_id']) for p_obj in p_objects]
    top_fa_status = [p_obj[4]['status'] if 'status' in p_obj[4] else 'H' for p_obj in p_objects]

    players_totals_query = f"SELECT * FROM players_season_totals WHERE yahoo_id IN {tuple(top_fa_ids)};"
    players_schedule_query = f"SELECT * FROM full_players_schedule WHERE yahoo_id IN {tuple(top_fa_ids)};"

    full_players_totals = pd.read_sql_query(players_totals_query, engine, index_col='yahoo_id')
    full_players_schedule = pd.read_sql_query(players_schedule_query, engine, index_col=['yahoo_id', 'full_name'])

    stats_cols = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
    numeric_cols = [col for col in full_players_totals.columns if col not in ['full_name', 'status', 'team']]
    full_players_totals[numeric_cols] = full_players_totals[numeric_cols].apply(pd.to_numeric, errors='coerce')
    full_players_totals[stats_cols] = full_players_totals[stats_cols].div(full_players_totals['GP'], axis=0)
    full_players_avg = full_players_totals[['full_name'] + stats_cols]

    full_players_schedule.columns = [datetime.datetime.strptime(col, '%Y-%m-%d') for col in
                                     full_players_schedule.columns]

    fetched_dates = ((full_players_schedule.columns <= pd.to_datetime(end_date)) &
                     (full_players_schedule.columns >= pd.to_datetime(start_date)))

    fetched_players_schedule = full_players_schedule.loc[:, fetched_dates]
    fetched_players_schedule.loc[:, ['number_of_games']] = fetched_players_schedule.apply(lambda x: x.notnull().sum(), axis=1)

    for name in top_fa_names:
        if name not in full_players_avg.full_name.values:
            print(f"{name} not in full_players_avg")

    stats_cols = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
    fa_averages = full_players_avg[full_players_avg.index.isin(top_fa_ids)]
    fa_averages.loc[:, ['status']] = fa_averages.index.map(dict(zip(top_fa_ids, top_fa_status)))
    fa_averages = fa_averages.merge(fetched_players_schedule, left_index=True, right_index=True)
    fa_averages = fa_averages[fa_averages['status'] != 'INJ']
    num_games_vector = fa_averages.loc[:, ['number_of_games']].values
    current_team_averages = fa_averages[stats_cols]

    fa_projections = current_team_averages.mul(num_games_vector, axis=0)
    fa_projections = fa_projections[['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']]
    fa_projections.fillna(0, inplace=True)
    fa_projections = fa_projections[~(fa_projections == 0).all(axis=1)]
    fa_projections.index = [idx[1] for idx in fa_projections.index]
    fa_projections = fa_projections.round(1)

    return fa_projections


if __name__ == '__main__':
    engine = init_db_config(path_to_db_config='../config.ini')

    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)

    week = 12
    for league_name in ["Ootan", "Sheniuk"]:
        sc, lg, league_id, current_week, _, _ = init_configuration(league_name=league_name, week=week, from_file="../oauth2.json")
        best_FA_pickup(sc, engine, lg, league_id, plot=True, current_week=current_week, league_name=league_name)
