import datetime
import logging, sqlalchemy
import pandas as pd
from yahoo_oauth import OAuth2
from sqlalchemy.dialects.postgresql import insert

from utils import init_db_config, run_yahoo_api_concurrently, convert_id_to_cat


def insert_on_conflict_nothing(table, conn, keys, data_iter):
    """Helper function for inserting data to DB with on conflict do nothing"""
    data = [dict(zip(keys, row)) for row in data_iter]
    stmt = insert(table.table).values(data).on_conflict_do_nothing(index_elements=['yahoo_id', 'date'])
    result = conn.execute(stmt)
    return result.rowcount


def update_players_daily_stats(date: str, players_ids: list[str]):
    """Update players stats for a given date to the DB"""
    url_base = 'https://fantasysports.yahooapis.com/fantasy/v2/players;player_keys='
    url_end = f'/stats;type=date;date={date}'
    players_ids_lists = [players_ids[i:i + 24] for i in range(0, len(players_ids), 24)]
    urls = [url_base + ','.join([f"nba.p.{id}" for id in subset]) + url_end for subset in players_ids_lists]
    responses = [res for res in run_yahoo_api_concurrently(sc, urls) if isinstance(res, dict)]
    try:
        fetched_responses = [list(res.values())[0]['players'] for res in responses]
    except KeyError:
        print(f'No stats for {date}')
        return

    players_objects = [player for subset in fetched_responses for player in subset.values() if isinstance(player, dict)]
    all_players_totals = []
    for player_object in players_objects:
        player_info, player_stats = player_object['player']
        name_idx = [i for i, x in enumerate(player_info) if 'name' in x]
        id_idx = [i for i, x in enumerate(player_info) if 'player_id' in x]
        injury_idx = [i for i, x in enumerate(player_info) if 'status' in x]

        player_name = player_info[name_idx[0]]['name']['full'] if name_idx else None
        player_id = player_info[id_idx[0]]['player_id'] if id_idx else None
        player_injury_status = player_info[injury_idx[0]]['status'] if injury_idx else 'H'

        player_stats_to_val = {stat['stat']['stat_id']: stat['stat']['value'] for stat in
                               player_stats['player_stats']['stats']}
        players_stats_cat = {convert_id_to_cat(stat_id): stat_val for stat_id, stat_val in
                             player_stats_to_val.items()}
        players_stats_cat['MP'] = '0' if players_stats_cat['MP'] == '-' else players_stats_cat['MP']

        temp_dict = {'yahoo_id': player_id, 'date': date, 'full_name': player_name,
                     'injury_status': player_injury_status}

        temp_dict.update(players_stats_cat)
        temp_dict.pop(None, None)
        all_players_totals.append(temp_dict)

    df = pd.DataFrame(all_players_totals)

    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df['MP'] = df['MP'].apply(lambda x: int(x.split(':')[0]))
    numeric_cols = [col for col in df.columns if col not in ['yahoo_id', 'date', 'full_name', 'injury_status']]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df = df[df['MP'] != 0]
    # df.to_sql('players_history_stats_daily', engine, if_exists='append', index=False, method=insert_on_conflict_nothing)
    df.to_sql('players_history_stats_daily', engine, if_exists='append', index=False)


def check_missing_dates_players_stats(engine, final_cup_date='2023-12-09'):
    """Check for missing dates in the DB and return a list of dates that are missing"""
    full_players_schedule = pd.read_sql('full_players_schedule', engine, index_col=['yahoo_id', 'full_name'])
    full_players_schedule.columns = pd.to_datetime(full_players_schedule.columns)
    full_players_schedule = full_players_schedule.loc[:, full_players_schedule.columns < pd.to_datetime('today').floor('d')]
    schedule_dates = [date.strftime("%Y-%m-%d") for date in full_players_schedule.columns.tolist()
                      if full_players_schedule[date].notna().any()]

    players_history_stats_daily = pd.read_sql('players_history_stats_daily', engine)[['yahoo_id', 'date']]
    captured_stats_dates = [date.strftime("%Y-%m-%d") for date in players_history_stats_daily['date'].unique()]
    captured_stats_dates = captured_stats_dates[:-1]
    missing_dates = [date for date in schedule_dates if date not in captured_stats_dates and date != final_cup_date]
    #
    return missing_dates


def update_players_season_totals_and_info(sc, engine):
    """Update players season totals and personal info to the DB"""
    players_ids_df = pd.read_sql_table('players_personal_info', engine)
    players_ids = players_ids_df['yahoo_id'].tolist()

    url_base = 'https://fantasysports.yahooapis.com/fantasy/v2/players;player_keys='
    players_ids_lists = [players_ids[i:i + 24] for i in range(0, len(players_ids), 24)]
    urls = [url_base + ','.join([f"nba.p.{id}" for id in subset]) + '/stats' for subset in players_ids_lists]

    responses = run_yahoo_api_concurrently(sc, urls)

    all_players_objects = [list(res['fantasy_content']['players'].values()) for res in responses]
    all_players_lists = [player for sublist in all_players_objects for player in sublist]
    all_players_totals = []
    all_players_info = []
    for player_obj in all_players_lists:
        if not isinstance(player_obj, dict):
            continue

        player_info, player_stats = player_obj['player']

        name_idx = [i for i, x in enumerate(player_info) if 'name' in x]
        id_idx = [i for i, x in enumerate(player_info) if 'player_id' in x]
        team_idx = [i for i, x in enumerate(player_info) if 'editorial_team_full_name' in x]
        injury_idx = [i for i, x in enumerate(player_info) if 'status' in x]

        player_name = player_info[name_idx[0]]['name']['full'] if name_idx else None
        player_id = player_info[id_idx[0]]['player_id'] if id_idx else None
        player_team = player_info[team_idx[0]]['editorial_team_full_name'] if team_idx else None
        player_injury_status = player_info[injury_idx[0]]['status'] if injury_idx else 'H'

        player_stats_to_val = {stat['stat']['stat_id']: stat['stat']['value'] for stat in
                               player_stats['player_stats']['stats']}
        players_stats_cat = {convert_id_to_cat(stat_id): stat_val for stat_id, stat_val in
                             player_stats_to_val.items()}

        players_stats_cat.pop(None, None)
        players_stats_cat['yahoo_id'] = player_id
        players_stats_cat['full_name'] = player_name
        all_players_totals.append(players_stats_cat)
        all_players_info.append({'yahoo_id': player_id, 'full_name': player_name,
                                 'team': player_team, 'injury_status': player_injury_status})

    all_players_info_df = pd.DataFrame(all_players_info)
    all_players_totals_df = pd.DataFrame(all_players_totals)

    duplicated_players_totals = all_players_totals_df[all_players_totals_df.duplicated(subset=['yahoo_id'], keep=False)]
    duplicated_players_info = all_players_info_df[all_players_info_df.duplicated(subset=['yahoo_id'], keep=False)]
    assert len(duplicated_players_totals) == 0, f"Found duplicated players in totals: {duplicated_players_totals}"

    all_players_totals_df.to_sql('players_season_totals', engine, if_exists='replace', index=False)
    all_players_info_df.to_sql('players_personal_info', engine, if_exists='replace', index=False)


if __name__ == '__main__':
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    logging.disable(logging.WARNING)

    engine = init_db_config(path_to_db_config='../config.ini')
    sc = OAuth2(None, None, from_file='../oauth2.json')

    update_players_season_totals_and_info(sc, engine)
    all_players_info = pd.read_sql('players_personal_info', engine)
    full_players_schedule = pd.read_sql('full_players_schedule', engine, index_col=['yahoo_id', 'full_name'])

    missing_dates = check_missing_dates_players_stats(engine)
    for date in missing_dates:
        if date not in full_players_schedule.columns:
            continue
        playing_players = full_players_schedule[~pd.isna(full_players_schedule[date])].index.tolist()
        playing_players_ids = [player[0] for player in playing_players]
        print(f"Updating {len(playing_players_ids)} players' stats for {date}")
        update_players_daily_stats(date, playing_players_ids)
