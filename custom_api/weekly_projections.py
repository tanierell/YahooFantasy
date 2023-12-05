import os
import time
import pytz
import pickle
import datetime
import numpy as np
import pandas as pd
import concurrent.futures

import nba_api.stats.endpoints as nba_endpoints

from NBA_fantasy.yahoo.utils import (fetch_teams_roster_ids, convert_id_to_cat,
                                     init_configuration, fetch_current_week_league_schedule)


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


def players_projections_current_week(sc, lg, league_id, end_date, current_week, path_to_db):
    full_players_avg = pickle.load(open(f"{path_to_db}/players_averages/players_avg_df.pkl", 'rb'))

    ect_time = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
    today_date = datetime.datetime.combine(ect_time, datetime.time())
    full_players_schedule = pickle.load(open(f"{path_to_db}/schedule/full_players_schedule.pkl", 'rb'))
    fetched_dates = ((full_players_schedule.columns <= pd.to_datetime(end_date, format='%Y-%m-%d')) &
                     (full_players_schedule.columns >= pd.to_datetime(today_date, format='%Y-%m-%d')))
    fetched_players_schedule = full_players_schedule.loc[:, fetched_dates]
    fetched_players_schedule.loc[:, ['number_of_games']] = fetched_players_schedule.sum(axis=1)

    rosters_data = fetch_teams_roster_ids(sc, lg, datetime_obj=today_date, league_id=league_id)
    league_matchups_names, league_matchups_status = get_weekly_matchup_status(lg, current_week)
    stats_cols = ['FGM', 'FGA', 'FTM', 'FTA', 'FG3M', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    teams_projections = {}

    for team_name, names_ids_statutes in rosters_data.items():
        players_names = names_ids_statutes['names']
        players_status = names_ids_statutes['status']
        current_team_averages = full_players_avg[full_players_avg.index.isin(players_names)]
        current_team_averages.loc[:, ['status']] = current_team_averages.index.map(dict(zip(players_names, players_status)))
        current_team_averages = current_team_averages.merge(fetched_players_schedule, left_index=True, right_index=True)
        current_team_averages = current_team_averages[current_team_averages['status'] != 'INJ']
        num_games_vector = current_team_averages.loc[:, ['number_of_games']].values
        current_team_averages = current_team_averages[stats_cols]
        team_proj = current_team_averages.mul(num_games_vector, axis=0)
        team_proj.rename(columns={'TOV': 'TO', 'FG3M': '3PTM', 'STL': 'ST'}, inplace=True)

        team_acc_dict = league_matchups_status[team_name]
        team_acc_stats = [float(team_acc_dict[stat]) if stat in team_acc_dict else '-' for stat in team_proj.columns]
        team_proj.loc['Accumulated'] = team_acc_stats
        team_proj.loc['Total'] = team_proj.select_dtypes(include=[np.number]).sum(axis=0)
        team_proj['FG%'] = team_proj['FGM'] / team_proj['FGA']
        team_proj['FT%'] = team_proj['FTM'] / team_proj['FTA']

        team_proj.drop(columns=['FGM', 'FGA', 'FTM', 'FTA'], inplace=True)
        team_proj = team_proj[['FG%', 'FT%', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']]
        team_proj.fillna(0, inplace=True)
        team_proj = team_proj[~(team_proj == 0).all(axis=1)]

        teams_projections[team_name] = team_proj

    return teams_projections, league_matchups_names


def weekly_matchups_projections(sc, lg, league_id, end_date, league_name, current_week, output_filename=None, path_to_db='../local_db'):
    """
    used to get the projections of the players in the given dates, based on their season average
    we fetch the data of today's players, and fetch data along the given dates for them
    """
    projections_by_team, league_matchups_names = players_projections_current_week(sc, lg, league_id, end_date,
                                                                                  current_week, path_to_db=path_to_db)

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
    # league_name = "Ootan"
    league_name = "Sheniuk"
    week = 7
    df = fetch_current_week_league_schedule(week=week)
    sc, lg, league_id, current_week, _, end_date = init_configuration(league_name=league_name, week=week, from_file='../oauth2.json')
    output_filename = f"../outputs/Excels/{league_name}/week-{current_week}_projections.xlsx"
    weekly_matchups_projections(sc=sc, lg=lg, league_id=league_id, end_date=end_date, league_name=league_name,
                                current_week=current_week, output_filename=output_filename, path_to_db='../local_db')