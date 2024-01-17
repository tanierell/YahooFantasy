import logging
from yahoo_oauth import OAuth2
import pandas as pd
from utils import init_db_config, run_yahoo_api_concurrently


def get_players_current_ratings(sc, engine, league_id, top_k):
    urls = [f'https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/players;sort=AR;start={start}'
            for start in range(0, top_k, 25)]
    responses = [res['fantasy_content']['league'] for res in run_yahoo_api_concurrently(sc, urls) if isinstance(res, dict)]

    all_players_objects = [list(res[1]['players'].values()) for res in responses if isinstance(res[1]['players'], dict)]
    all_players_lists = [player for sublist in all_players_objects for player in sublist]
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
    current_players_db = pd.read_sql_table('players_personal_info', engine)
    added_players = all_players_df[~all_players_df['yahoo_id'].isin(current_players_db['yahoo_id'])]
    # added_players.to_sql('players_personal_info', engine, if_exists='append', index=False)





if __name__ == '__main__':
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    logging.disable(logging.WARNING)

    engine = init_db_config(path_to_db_config='config.ini')
    sc = OAuth2(None, None, from_file='oauth2.json')
    players_totals_query = f"SELECT * FROM players_season_totals;"
    players_schedule_query = f"SELECT * FROM full_players_schedule;"

    get_players_current_ratings(sc, engine, league_id='428.l.2540', top_k=25)