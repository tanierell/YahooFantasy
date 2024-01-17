import logging
import requests
import pandas as pd
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import insert
from yahoo_oauth import OAuth2

from utils import init_db_config, run_yahoo_api_concurrently


def insert_on_conflict_nothing(table, conn, keys, data_iter):
    """Helper function for inserting data to DB with on conflict do nothing"""
    data = [dict(zip(keys, row)) for row in data_iter]
    stmt = insert(table.table).values(data).on_conflict_do_nothing(index_elements=['yahoo_id', 'date'])
    result = conn.execute(stmt)
    return result.rowcount


def update_new_players_info(league_id, engine, sc):
    urls = [f'https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/players;start={start}'
            for start in range(0, 800, 24)]

    responses = [res['fantasy_content']['league'] for res in run_yahoo_api_concurrently(sc, urls)]

    all_players_objects = [res[1]['players'] for res in responses]
    all_players_objects = [list(obj.values()) for obj in all_players_objects if isinstance(obj, dict)]
    all_players_lists = [player for sublist in all_players_objects for player in sublist if isinstance(player, dict)]
    all_players_info = []
    for player_obj in all_players_lists:
        if not isinstance(player_obj, dict):
            continue

        player_info = player_obj['player'][0]

        name_idx = [i for i, x in enumerate(player_info) if 'name' in x]
        id_idx = [i for i, x in enumerate(player_info) if 'player_id' in x]
        team_idx = [i for i, x in enumerate(player_info) if 'editorial_team_full_name' in x]
        injury_idx = [i for i, x in enumerate(player_info) if 'status' in x]

        player_name = player_info[name_idx[0]]['name']['full'] if name_idx else None
        player_id = player_info[id_idx[0]]['player_id'] if id_idx else None
        player_team = player_info[team_idx[0]]['editorial_team_full_name'] if team_idx else None
        player_injury_status = player_info[injury_idx[0]]['status'] if injury_idx else 'H'
        all_players_info.append({'yahoo_id': player_id, 'full_name': player_name,
                                 'team': player_team, 'injury_status': player_injury_status})

    all_players_df = pd.DataFrame(all_players_info)
    all_players_df.drop_duplicates(subset=['yahoo_id'], inplace=True)
    all_players_df.to_sql('players_personal_info', engine, if_exists='replace', index=False)

    # current_players_db = pd.read_sql_table('players_personal_info', engine)
    # added_players = all_players_df[~all_players_df['yahoo_id'].isin(current_players_db['yahoo_id'])]
    # added_players.to_sql('players_personal_info', engine, if_exists='append', index=False)


def init_players_schedule(engine):
    """Create a table with all players schedule for the season. Used for updating players schedule in case of trades"""
    players_info_df = pd.read_sql_table('players_personal_info', engine)
    teams_schedule_df = pd.read_sql_table('full_teams_schedule', engine)

    teams = sorted(pd.unique(teams_schedule_df[['home_team', 'away_team']].values.ravel('K')))
    new_df = pd.DataFrame(index=pd.unique(teams_schedule_df['game_time'].dt.date), columns=teams)

    for date, row in new_df.iterrows():
        full_schedule_date = teams_schedule_df[teams_schedule_df['game_time'].dt.date == date]
        game_times = full_schedule_date['game_time'].dt.strftime('%H:%M').values.tolist()
        home_teams = full_schedule_date['home_team'].values.tolist()
        away_teams = full_schedule_date['away_team'].values.tolist()

        new_df.loc[date, home_teams] = list(zip(game_times, [f"vs. {away_team}" for away_team in away_teams]))
        new_df.loc[date, away_teams] = list(zip(game_times, [f"@ {home_team}" for home_team in home_teams]))

    teams_schedule_reformatted = new_df.transpose()
    players_info_df.set_index('team', inplace=True)
    merged_df = players_info_df.merge(teams_schedule_reformatted, how='left', left_index=True, right_index=True)
    merged_df.reset_index(inplace=True)

    merged_df = merged_df[['yahoo_id', 'full_name'] + teams_schedule_reformatted.columns.tolist()]
    merged_df.to_sql('full_players_schedule', engine, if_exists='replace', index=False)


def init_nba_schedule(engine):
    """Create a table with all NBA games for the season. Updated once a year, for all the teams schedule"""
    url_base = 'https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2023/league/00_full_schedule_week_tbds.json'
    res = requests.get(url_base).json()
    all_matchups = []
    for game in res['lscd']:
        for game_obj in game['mscd']['g']:
            game_time = game_obj['etm']
            h_team = game_obj['h']['tc'] + ' ' + game_obj['h']['tn']
            v_team = game_obj['v']['tc'] + ' ' + game_obj['v']['tn']
            gweek = game_obj['gweek']
            if gweek is not None:
                all_matchups.append([game_time, h_team, v_team])

    nba_schedule = pd.DataFrame(all_matchups, columns=['game_time', 'home_team', 'away_team'])
    nba_schedule['game_time'] = pd.to_datetime(nba_schedule['game_time'])
    nba_schedule.sort_values(by='game_time', inplace=True)

    nba_schedule.to_sql('full_teams_schedule', engine, if_exists='replace', index=False, dtype={'game_time': DateTime})


if __name__ == '__main__':
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    logging.disable(logging.WARNING)

    engine = init_db_config(path_to_db_config='../config.ini')
    sc = OAuth2(None, None, from_file='../oauth2.json')
    update_new_players_info('428.l.2540', engine, sc)
    init_nba_schedule(engine)
    init_players_schedule(engine)
