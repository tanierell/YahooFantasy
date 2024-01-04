import time, requests
import nba_api.stats.endpoints as nba_endpoints
import pandas as pd
import datetime
import concurrent.futures
from sqlalchemy import create_engine
from utils import init_configuration, convert_id_to_cat, run_yahoo_api_concurrently, init_db_config

if __name__ == '__main__':
    league_name = "Sheniuk"
    sc, lg, league_id, current_week, start_date, end_date = init_configuration(league_name, week=11,
                                                                               from_file='oauth2.json')
    engine = init_db_config(path_to_db_config='postgreSQL_init/config.ini')
    players_ids_df = pd.read_sql_table('players_ids_conversions', engine)
    players_ids = players_ids_df['yahoo_id'].tolist()

    url_base = 'https://fantasysports.yahooapis.com/fantasy/v2/players;player_keys='
    k = 24
    players_ids_lists = [players_ids[i:i + k] for i in range(0, len(players_ids), k)]
    url_end = '/stats;type=week;week=11'
    responses = []
    urls = []
    for players_ids_list in players_ids_lists:
        urls.append(url_base + ','.join([f'nba.p.{player_id}' for player_id in players_ids_list]) + url_end)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_yahoo_api_concurrently, sc, url) for url in urls[:]]
        responses += [future.result() for future in concurrent.futures.as_completed(futures)]
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
    columns = ['yahoo_id', 'full_name'] + [col for col in all_players_totals_df.columns if
                                           col not in ['yahoo_id', 'full_name']]
