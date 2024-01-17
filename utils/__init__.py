import logging
import datetime
import configparser
import pandas as pd
import concurrent.futures
import matplotlib.pyplot as plt

from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

from sqlalchemy import create_engine

logging.disable(logging.DEBUG)
logging.disable(logging.INFO)
logging.disable(logging.WARNING)


def init_configuration(league_name, week=None, from_file='oauth2.json'):
    sc = OAuth2(None, None, from_file=from_file)
    gm = yfa.Game(sc, 'nba')
    sheniuk_id, dor_id = '428.l.2540', '428.l.114976'
    league_id = dor_id if league_name == "Ootan" else sheniuk_id
    lg = gm.to_league(league_id)
    current_week = lg.current_week() if week is None else week
    start_date, end_date = lg.week_date_range(current_week)

    return sc, lg, league_id, current_week, start_date, end_date


def fetch_roster_ids_by_dates(sc, datetime_objects, league_id, fetch_k_ids=None, fetch_k_teams=12):
    """Fetch team roster for week and day. Returns df with team name, player id and date."""
    url = f'https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/teams'
    kwargs = {'params': {'format': 'json'}, 'allow_redirects': True}
    with sc.session as s:
        res = s.request('GET', url, **kwargs)
        sc.session.close()

    teams = list(res.json()['fantasy_content']['league'][1]['teams'].values())
    teams_names_keys = {team['team'][0][2]['name']: team['team'][0][0]['team_key']
                        for team in teams[:fetch_k_teams] if isinstance(team, dict)}
    url_base = 'https://fantasysports.yahooapis.com/fantasy/v2/team/'
    urls = [url_base + team_key + f'/roster;date={date_obj.strftime("%Y-%m-%d")}'
            for team_key in teams_names_keys.values() for date_obj in datetime_objects]
    responses = run_yahoo_api_concurrently(sc, urls)
    results = {'yahoo_id': [], 'date': [], 'team_name': [], 'full_name': [], 'status': []}
    for res in responses:
        team_name = res['fantasy_content']['team'][0][2]['name']
        roster_object = list(res['fantasy_content']['team'][1]['roster']['0']['players'].values())
        fetch_k_ids = len(roster_object) if fetch_k_ids is None else fetch_k_ids
        players_ids = [player['player'][0][1]['player_id'] for player in roster_object if isinstance(player, dict)][:fetch_k_ids]
        players_names = [player['player'][0][2]['name']['full'] for player in roster_object if isinstance(player, dict)][:fetch_k_ids]
        players_status = [player['player'][0][4]['status'] if 'status' in player['player'][0][4] else 'H'
                          for player in roster_object if isinstance(player, dict)][:fetch_k_ids]
        fetched_date = [res['fantasy_content']['team'][1]['roster']['date'] for _ in range(len(players_ids))][:fetch_k_ids]

        results['yahoo_id'].extend(players_ids)
        results['date'].extend(fetched_date)
        results['status'].extend(players_status)
        results['full_name'].extend(players_names)
        results['team_name'].extend([team_name for _ in range(len(players_ids))])

    return pd.DataFrame(results)


def get_teams_stats_date_range(sc, engine, dates_list, league_id, plot=False):
    """ Fetch team stats for dates in dates_tuples. Returns pandas DataFrame with team stats of the sum of all dates. """
    rosters_by_date_df = fetch_roster_ids_by_dates(sc, dates_list, league_id, fetch_k_ids=10, fetch_k_teams=12)
    query_ids = tuple(set(rosters_by_date_df['yahoo_id'].tolist()))
    query_dates = tuple(set(rosters_by_date_df['date'].tolist()))
    query = f"SELECT * FROM players_history_stats_daily WHERE yahoo_id IN {query_ids} AND date IN {query_dates}"
    fetched_stats = pd.read_sql_query(query, engine)
    rosters_by_date_df['date'] = pd.to_datetime(rosters_by_date_df['date']).dt.date
    rosters_by_date_df.drop(['status', 'full_name'], axis=1, inplace=True)
    final_results = fetched_stats.merge(rosters_by_date_df, on=['yahoo_id', 'date'], how='left')
    numeric_cols = ['FGA', 'FGM', 'FTA', 'FTM', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO', 'GP']
    final_results = final_results.groupby(['team_name', 'full_name'])[numeric_cols].sum().fillna(0).reset_index(level=1)

    weekly_summarized_df = {team_name: team_df.set_index('full_name') for team_name, team_df in final_results.groupby(level=0)}
    for team_name, team_weekly_sum_df in weekly_summarized_df.items():
        if plot:
            column_percentages = team_weekly_sum_df.divide(team_weekly_sum_df.sum(axis=0), axis=1)
            column_percentages['TO'] *= -1
            weighted_avg_impact = column_percentages.mean(axis=1)
            filtered_players = weighted_avg_impact.sort_values(ascending=False)[:20]
            filtered_players = filtered_players[filtered_players >= 0.01]

            plt.figure(figsize=(8, 8))
            plt.pie(filtered_players, labels=filtered_players.index, autopct='%1.1f%%', startangle=140)

            plt.axis('equal')
            plt.show()

        team_weekly_sum_df.loc['Total'] = team_weekly_sum_df.sum()
        team_weekly_sum_df.insert(2, 'FG%', team_weekly_sum_df['FGM'] / team_weekly_sum_df['FGA'])
        team_weekly_sum_df.insert(5, 'FT%', team_weekly_sum_df['FTM'] / team_weekly_sum_df['FTA'])

        team_weekly_sum_df['FG%'] = team_weekly_sum_df['FG%'].apply(lambda x: f"{x:.3f}" if x > 0 else '0')
        team_weekly_sum_df['FT%'] = team_weekly_sum_df['FT%'].apply(lambda x: f"{x:.3f}" if x > 0 else '0')

        weekly_summarized_df[team_name] = team_weekly_sum_df

    return weekly_summarized_df


def convert_id_to_cat(stat_id):
    """Convert stat id to category. Returns category name. expects stat_id to be string."""
    stat_id_to_category = {0: 'GP', 2: 'MP', 3: 'FGA', 4: 'FGM', 5: 'FG%', 6: 'FTA', 7: 'FTM', 8: 'FT%', 9: '3PA', 10: '3PTM',
                           11: '3P%', 12: 'PTS', 15: 'REB', 16: 'AST', 17: 'ST', 18: 'BLK', 19: 'TO', 9004003: 'FGM/FGA', 9007006: 'FTM/FTA'}

    return stat_id_to_category.get(int(stat_id), None)


def concurrent_helper_function(sc, url):
    kwargs = {'params': {'format': 'json'}, 'allow_redirects': True}
    with sc.session as s:
        res = s.get(url, **kwargs).json()
    s.close()
    return res


def run_yahoo_api_concurrently(sc, urls):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(concurrent_helper_function, sc, url) for url in urls]
        responses = [future.result() for future in concurrent.futures.as_completed(futures)]

    return responses


def init_db_config(path_to_db_config='../config.ini'):
    config = configparser.ConfigParser()
    config.read(path_to_db_config)

    config = config['postgreSQL Configurations']
    username = config['username']
    password = config['password']
    hostname = config['hostname']
    dbname = config['dbname']
    port = config['port']

    db_string = f"postgresql+psycopg2://{username}:{password}@{hostname}/{dbname}"
    engine = create_engine(db_string)

    return engine


if __name__ == '__main__':
    league_name = "Sheniuk"
    sc, lg, league_id, current_week, start_date, end_date = init_configuration(league_name, week=11, from_file='../oauth2.json')
    engine = init_db_config(path_to_db_config='../config.ini')
    dates = [start_date + datetime.timedelta(days=i) for i in range(7)]
