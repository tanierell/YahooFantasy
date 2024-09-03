import logging

import pytz
import datetime
import numpy as np
import pandas as pd


from utils import (convert_id_to_cat, init_configuration, init_db_config, fetch_roster_ids_by_dates, load_players_avg_by_date)


def get_weekly_matchup_status(lg, current_week):
    league_matchups_raw = lg.matchups(current_week)['fantasy_content']['league'][1]['scoreboard']['0']['matchups']
    league_matchups_status = {}
    league_matchups_names = []
    for matchup in league_matchups_raw.values():
        if not isinstance(matchup, dict):
            continue
        team_a_name = matchup['matchup']['0']['teams']['0']['team'][0][2]['name']
        team_b_name = matchup['matchup']['0']['teams']['1']['team'][0][2]['name']

        team_a_stats = [stat['stat'] for stat in
                        matchup['matchup']['0']['teams']['0']['team'][1]['team_stats']['stats']]
        team_b_stats = [stat['stat'] for stat in
                        matchup['matchup']['0']['teams']['1']['team'][1]['team_stats']['stats']]

        team_a_conversion_stats = {convert_id_to_cat(stat['stat_id']): stat['value'] for stat in team_a_stats}
        team_b_conversion_stats = {convert_id_to_cat(stat['stat_id']): stat['value'] for stat in team_b_stats}

        needed_stats = ['FGM/FGA', 'FTM/FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
        team_a_conversion_stats = {stat: team_a_conversion_stats[stat] for stat in needed_stats}
        team_b_conversion_stats = {stat: team_b_conversion_stats[stat] for stat in needed_stats}

        team_a_conversion_stats = {k: v if v != '' else 0 for k, v in team_a_conversion_stats.items()}
        team_b_conversion_stats = {k: v if v != '' else 0 for k, v in team_b_conversion_stats.items()}

        for stat in ['FGM/FGA', 'FTM/FTA']:
            made, attempt = stat.split('/')
            made_a, attempt_a = team_a_conversion_stats[stat].split('/')
            made_b, attempt_b = team_b_conversion_stats[stat].split('/')
            '''check if len of values is 0, and set to 0 if does'''
            if len(made_a) == 0:
                made_a, attempt_a = 0, 0
            if len(made_b) == 0:
                made_b, attempt_b = 0, 0

            team_a_conversion_stats[made] = float(made_a)
            team_a_conversion_stats[attempt] = float(attempt_a)
            team_b_conversion_stats[made] = float(made_b)
            team_b_conversion_stats[attempt] = float(attempt_b)
            del team_a_conversion_stats[stat]
            del team_b_conversion_stats[stat]

        league_matchups_names.append((team_a_name, team_b_name))
        league_matchups_status[team_a_name] = team_a_conversion_stats
        league_matchups_status[team_b_name] = team_b_conversion_stats

    return league_matchups_names, league_matchups_status


def fetch_custom_dates_lists(start_date, end_date, days=None, months=None):
    if months is not None and days is not None:
        start_date = datetime.datetime.now() - datetime.timedelta(days=30 * months + days)
        end_date = datetime.datetime.now()

    else:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    dates_list = pd.date_range(start_date, end_date, freq='D')
    dates_list = [date.date() for date in dates_list]
    return dates_list


def players_projections_current_week(sc, lg, league_id, end_date, current_week, engine, players_stats_method):
    ect_time = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
    today_date = datetime.datetime.combine(ect_time, datetime.time())

    rosters_data = fetch_roster_ids_by_dates(sc=sc, datetime_objects=[today_date], league_id=league_id)
    query_ids = tuple(set(rosters_data['yahoo_id'].tolist()))

    players_custom_query = f"SELECT * FROM players_history_stats_daily WHERE yahoo_id IN {query_ids};"
    players_totals_query = f"SELECT * FROM players_season_totals WHERE yahoo_id IN {query_ids};"
    players_schedule_query = f"SELECT * FROM full_players_schedule WHERE yahoo_id IN {query_ids};"

    query = players_custom_query if players_stats_method == 'custom_dates' else players_totals_query
    full_players_stats = pd.read_sql_query(query, engine, index_col='yahoo_id')
    full_players_stats_avg = load_players_avg_by_date(full_players_stats, players_stats_method)
    full_players_schedule = pd.read_sql_query(players_schedule_query, engine, index_col=['yahoo_id', 'full_name'])
    full_players_schedule.columns = [datetime.datetime.strptime(col, '%Y-%m-%d') for col in
                                     full_players_schedule.columns]

    proj_fetched_dates = ((full_players_schedule.columns <= pd.to_datetime(end_date, format='%Y-%m-%d')) &
                          (full_players_schedule.columns >= today_date))

    fetched_players_schedule = full_players_schedule.loc[:, proj_fetched_dates]
    fetched_players_schedule.loc[:, ['number_of_games']] = fetched_players_schedule.apply(lambda x: x.notnull().sum(), axis=1)

    league_matchups_names, league_matchups_status = get_weekly_matchup_status(lg, current_week)
    # league_matchups_names = [('TheRealTani', "The Lord")]
    # league_matchups_status = {'TheRealTani': {'FGM': 0, 'FGA': 0, 'FTM': 0, 'FTA': 0, '3PTM': 0, 'PTS': 0, 'REB': 0, 'AST': 0, 'ST': 0, 'BLK': 0, 'TO': 0},
    #                             "The Lord": {'FGM': 0, 'FGA': 0, 'FTM': 0, 'FTA': 0, '3PTM': 0, 'PTS': 0, 'REB': 0, 'AST': 0, 'ST': 0, 'BLK': 0, 'TO': 0}}
    teams_projections = {}

    for team_name, roster_info_df in rosters_data.groupby('team_name'):
        if team_name not in league_matchups_status:
            print(f"Team {team_name} is not in the league matchups, skipping")
            continue

        players_status = roster_info_df['status'].tolist()
        players_ids = roster_info_df['yahoo_id'].tolist()
        players_positions = roster_info_df['position'].tolist()
        current_team_averages = full_players_stats_avg[full_players_stats_avg.index.isin(players_ids)]
        current_team_averages.loc[:, ['status']] = current_team_averages.index.map(dict(zip(players_ids, players_status)))
        current_team_averages.loc[:, ['position']] = current_team_averages.index.map(dict(zip(players_ids, players_positions)))
        current_team_averages = current_team_averages.merge(fetched_players_schedule, left_index=True, right_on=['yahoo_id'])

        current_team_averages = current_team_averages[~(current_team_averages['status'].isin(['INJ']) |
                                                        current_team_averages['position'].isin(['IL+'])|
                                                        current_team_averages['position'].isin(['IL']))]

        num_games_vector = current_team_averages.loc[:, ['number_of_games']].values
        stats_cols = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
        current_team_averages = current_team_averages[stats_cols]
        team_proj = current_team_averages.mul(num_games_vector, axis=0)

        team_acc_dict = league_matchups_status[team_name]
        team_acc_stats = [float(team_acc_dict[stat]) if stat in team_acc_dict else '-' for stat in team_proj.columns]
        team_proj.loc['Accumulated'] = team_acc_stats
        # if team_name == "TheRealTani":
        #     included_players_mask = team_proj.loc[(team_proj.FTM / team_proj.FTA > 0.77) | (team_proj.REB > 40)]
        #     team_proj = team_proj.loc[included_players_mask.index]
        # if team_name == "LeTippex":
        #     included_players_mask = team_proj.loc[(team_proj.FTM / team_proj.FTA > 0.8)]
        #     '''calculate total based on these and accumulated'''
        #     team_proj.loc['Total'] = included_players_mask.select_dtypes(include=[np.number]).sum(axis=0) + team_proj.loc['Accumulated']
        #
        # else:
        #     team_proj.loc['Total'] = team_proj.select_dtypes(include=[np.number]).sum(axis=0)

        team_proj.loc['Total'] = team_proj.select_dtypes(include=[np.number]).sum(axis=0)
        team_proj['FG%'] = np.where(team_proj['FGA'] == 0, 0, team_proj['FGM'] / team_proj['FGA'])
        team_proj['FT%'] = np.where(team_proj['FTA'] == 0, 0, team_proj['FTM'] / team_proj['FTA'])

        players_index = current_team_averages.index.tolist()
        norm_fgp = np.where(team_proj.loc[players_index, 'FGA'] == 0, 0, team_proj.loc[players_index, 'FGM'] ** 2 / team_proj.loc[players_index, 'FGA'])
        norm_fgp /= sum(norm_fgp)
        norm_fgp = np.pad(norm_fgp, (0, 2), 'constant', constant_values=(np.nan, np.nan))
        norm_ftp = np.where(team_proj.loc[players_index, 'FTA'] == 0, 0, team_proj.loc[players_index, 'FTM'] ** 2 / team_proj.loc[players_index, 'FTA'])
        norm_ftp /= sum(norm_ftp)
        norm_ftp = np.pad(norm_ftp, (0, 2), 'constant', constant_values=(np.nan, np.nan))

        team_proj.drop(columns=['FGM', 'FGA', 'FTM', 'FTA'], inplace=True)
        team_proj.fillna(0, inplace=True)
        team_proj['FGP'] = norm_fgp
        team_proj['FTP'] = norm_ftp

        team_proj = team_proj[['FG%', 'FGP', 'FT%', 'FTP', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']]
        team_proj = team_proj[~(team_proj == 0).all(axis=1)]
        team_proj.index = [idx[1] if idx not in ['Total', 'Accumulated'] else idx for idx in team_proj.index]
        roundable_cols = [col for col in team_proj.columns if col not in ['FG%', 'FT%', 'FTP', 'FGP']]
        team_proj[roundable_cols] = team_proj[roundable_cols].round(1)
        teams_projections[team_name] = team_proj

    return teams_projections, league_matchups_names


def weekly_matchups_projections(sc, lg, league_id, end_date, league_name,
                                current_week, engine, players_stats_method, output_filename=None):
    """
    used to get the projections of the players in the given dates, based on their season average
    we fetch the data of today's players, and fetch data along the given dates for them
    """
    projections_by_team, league_matchups_names = players_projections_current_week(sc=sc, lg=lg, league_id=league_id,
                                                                                  end_date=end_date,
                                                                                  current_week=current_week, engine=engine,
                                                                                  players_stats_method=players_stats_method)

    if output_filename is None:
        output_filename = f"outputs/Excels/{league_name}/week-{current_week}_projections.xlsx"

    with pd.ExcelWriter(output_filename, engine='xlsxwriter') as writer:
        startcol = 0
        startrow = 0

        if 'Sheet1' not in writer.sheets:
            writer.book.add_worksheet('Sheet1')

        center_format = writer.book.add_format({'align': 'center', 'valign': 'vcenter'})
        bold_center_format = writer.book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})

        for matchup in league_matchups_names:
            team_a_name, team_b_name = matchup
            team_a_df, team_b_df = projections_by_team[team_a_name], projections_by_team[team_b_name]

            for team_name, team_df in [(team_a_name, team_a_df), (team_b_name, team_b_df)]:
                team_df['Player'] = [name if name not in ['Total', 'Accumulated'] else name for name in team_df.index]
                team_df.reset_index(drop=True, inplace=True)
                team_df = team_df[['Player'] + list(team_df.columns[:-1])]
                team_df = team_df.round(3)

                endcol = startcol + len(team_df.columns) - 1
                writer.sheets['Sheet1'].merge_range(startrow, startcol, startrow + 1, endcol, team_name,
                                                    bold_center_format)
                startrow += 2

                for col_num, value in enumerate(team_df.columns):
                    writer.sheets['Sheet1'].write(startrow, startcol + col_num, value, bold_center_format)
                    writer.sheets['Sheet1'].set_column(startcol + col_num, startcol + col_num, 15)  # Set column width

                for row_num, row in enumerate(team_df.values):
                    for col_num, value in enumerate(row):
                        value = '-' if pd.isnull(value) else value
                        cell_format = bold_center_format if team_df.iloc[row_num][
                                                                'Player'] == 'Total' else center_format
                        writer.sheets['Sheet1'].write(row_num + startrow + 1, startcol + col_num, value, cell_format)

                startrow -= 2
                startcol += len(team_df.columns) + 2

                if team_name == team_b_name:  # Reset for next matchup
                    startcol = 0
                    startrow += max(len(team_a_df), len(team_b_df)) + 5


if __name__ == '__main__':
    engine = init_db_config(path_to_db_config='../config.ini')

    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)

    week = 22
    for league_name in ["Ootan"]:
        sc, lg, league_id, current_week, _, end_date = init_configuration(league_name=league_name, week=week,
                                                                          from_file='../oauth2.json')
        output_filename = f"../outputs/Excels/{league_name}/week-{current_week}_projections.xlsx"
        weekly_matchups_projections(sc=sc, lg=lg, league_id=league_id, end_date=end_date, players_stats_method='custom_dates',
                                    league_name=league_name, current_week=current_week, engine=engine, output_filename=output_filename)