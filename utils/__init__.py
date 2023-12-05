import os
import pytz
import pickle
import requests
import datetime
import pandas as pd
import concurrent.futures
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa

import nba_api.stats.endpoints as nba_endpoints


def init_configuration(league_name, week=None, from_file='oauth2.json'):
    sc = OAuth2(None, None, from_file=from_file)
    gm = yfa.Game(sc, 'nba')
    sheniuk_id, dor_id = '428.l.2540', '428.l.114976'
    league_id = dor_id if league_name == "Ootan" else sheniuk_id
    lg = gm.to_league(league_id)
    current_week = lg.current_week() if week is None else week
    start_date, end_date = lg.week_date_range(current_week)

    return sc, lg, league_id, current_week, start_date, end_date


def fetch_player_average_concurrently(player_id: int, player_name: str, get_schedule: bool = False, path_to_db: str = '../local_db'):
    """Fetch player average stats for season, and schedule for player. Returns empty dict. this func saves the data to local_db"""
    reformatted_player_name = player_name.replace(' ', '_')
    player_season_average_obj = nba_endpoints.playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(
        player_id=player_id,
        season='2023-24',
        per_mode_detailed='PerGame').data_sets[0].data

    if get_schedule:
        player_prev_schedule = nba_endpoints.playergamelog.PlayerGameLog(player_id=player_id).get_data_frames()[0]
        player_next_schedule = nba_endpoints.playernextngames.PlayerNextNGames(player_id=player_id).get_data_frames()[0]
        if len(player_prev_schedule) == 0:
            print(f"Could not fetch previous schedule for player {player_name} with id {player_id}")
            player_prev_schedule = pd.DataFrame(
                columns=['GAME_DATE', 'HOME_TEAM_ABBREVIATION', 'VISITOR_TEAM_ABBREVIATION'])
        else:
            split_criterion = lambda game: pd.Series(game.split(' @ ')[::-1]) if '@' in game else pd.Series(
                game.split(' vs. '))
            player_prev_schedule[['HOME_TEAM_ABBREVIATION', 'VISITOR_TEAM_ABBREVIATION']] = player_prev_schedule[
                'MATCHUP'].apply(split_criterion)
            player_prev_schedule = player_prev_schedule[
                ['GAME_DATE', 'HOME_TEAM_ABBREVIATION', 'VISITOR_TEAM_ABBREVIATION']]

        player_next_schedule = player_next_schedule[
            ['GAME_DATE', 'HOME_TEAM_ABBREVIATION', 'VISITOR_TEAM_ABBREVIATION']]

        player_full_schedule = pd.concat([player_prev_schedule, player_next_schedule])
        player_full_schedule['GAME_DATE'] = pd.to_datetime(player_full_schedule['GAME_DATE'], format='%b %d, %Y')

        os.makedirs(f"{path_to_db}/schedule", exist_ok=True)
        with open(f"{path_to_db}/schedule/{reformatted_player_name}.pkl", "wb") as f:
            pickle.dump(player_full_schedule, f)

    start_date = datetime.datetime.combine(datetime.datetime.now(tz=pytz.timezone('US/Eastern')), datetime.time())

    needed_columns = ['FGM', 'FGA', 'FG3M', 'FTM', 'FTA', 'PTS', 'REB', 'AST',
                      'TOV', 'STL', 'BLK', 'player_id', 'player_name']
    if len(player_season_average_obj['data']) == 0:
        return {}
    else:
        player_season_avg_data = player_season_average_obj['data'][0] + [player_id, player_name]

    player_season_avg_columns = player_season_average_obj['headers'] + ['player_id', 'player_name']
    player_season_avg_dict = dict(zip(player_season_avg_columns, player_season_avg_data))
    player_dict = {k: player_season_avg_dict[k] for k in needed_columns}

    today_reformatted_date = start_date.strftime('%Y-%m-%d')
    os.makedirs(f"{path_to_db}/players_averages/{today_reformatted_date}", exist_ok=True)
    with open(f"{path_to_db}/players_averages/{today_reformatted_date}/{reformatted_player_name}.pkl", "wb") as f:
        pickle.dump(player_dict, f)

    return {}


def update_db_with_players_averages(path_to_db='../local_db', build_full_schedule=False):
    all_players_names = pickle.load(open(f"{path_to_db}/players_names_list.pkl", "rb"))
    nba_api_players_list = pickle.load(open(f"{path_to_db}/all_time_players_nba_api.pkl", "rb"))
    all_players_columns = ['player_id', 'first_name', 'last_name', 'full_name', 'is_active']
    all_time_players_df = pd.DataFrame(nba_api_players_list, columns=all_players_columns)[['player_id', 'full_name']]
    filtered_df = all_time_players_df[all_time_players_df['full_name'].str.contains('|'.join(all_players_names),
                                                                                    case=False, na=False)]
    start_date = datetime.datetime.combine(datetime.datetime.now(tz=pytz.timezone('US/Eastern')), datetime.time())
    today_reformatted_date = start_date.strftime('%Y-%m-%d')

    players_ids_names_schedule = []
    for player_id, player_name in zip(filtered_df['player_id'], filtered_df['full_name']):
        average_exist = os.path.exists(f"{path_to_db}/players_averages/{today_reformatted_date}/{player_name.replace(' ', '_')}.pkl")
        schedule_exist = os.path.exists(f"{path_to_db}/schedule/{player_name.replace(' ', '_')}.pkl")

        run_schedule = True if not schedule_exist else False
        if not average_exist:
            players_ids_names_schedule.append((player_id, player_name, run_schedule))

    # '''fetching only those without schedule - run this if want specific players schedule'''
    # players_ids_names_schedule = [player for player in players_ids_names_schedule if player[2]]

    print(f"Fetching {len(players_ids_names_schedule)} players")
    args = [(player_id, player_name, run_schedule, path_to_db)
            for player_id, player_name, run_schedule in players_ids_names_schedule]

    with concurrent.futures.ProcessPoolExecutor(max_workers=12) as executor:
        _ = [executor.submit(fetch_player_average_concurrently, *arg) for arg in args]

    db_dates = [date for date in os.listdir(f'{path_to_db}/players_averages') if date != 'players_avg_df.pkl']
    latest_day = max([datetime.datetime.strptime(date, '%Y-%m-%d') for date in db_dates]).strftime('%Y-%m-%d')

    players_averages = []
    for filename in os.listdir(f'{path_to_db}/players_averages/{latest_day}'):
        with open(f'{path_to_db}/players_averages/{latest_day}/{filename}', 'rb') as f:
            players_averages.append(pickle.load(f))

    players_avg_df = pd.DataFrame(players_averages).set_index('player_name')
    with open(f'{path_to_db}/players_averages/players_avg_df.pkl', 'wb') as f:
        pickle.dump(players_avg_df, f)

    if build_full_schedule:
        players_schedule_filenames = os.listdir(f'{path_to_db}/schedule')
        players_names = [filename.split('.pkl')[0].replace('_', ' ') for filename in players_schedule_filenames]
        start_date = datetime.datetime(2023, 10, 24)
        dates_columns = [start_date + datetime.timedelta(days=i) for i in range(200)]
        full_players_schedule = pd.DataFrame(columns=dates_columns, index=players_names)
        for filename in players_schedule_filenames:
            player_name = filename.split('.pkl')[0].replace('_', ' ')
            if '/' in player_name:
                player_name = player_name.split('/')[-1]

            with open(f'{path_to_db}/schedule/{filename}', 'rb') as f:
                player_schedule = pickle.load(f)
                game_dates = player_schedule['GAME_DATE']
                full_players_schedule.loc[player_name, game_dates] = 1

        full_players_schedule.fillna(0, inplace=True)
        full_players_schedule = full_players_schedule.loc[:, (full_players_schedule != 0).any(axis=0)]
        with open(f'{path_to_db}/schedule/full_players_schedule.pkl', 'wb') as f:
            pickle.dump(full_players_schedule, f)


def fetch_roster_data_concurrently(lg, team_key, team_name, datetime_obj):
    roster = lg.to_team(team_key).roster(week=None, day=datetime_obj)
    team_names_ids = [player['player_id'] for player in roster]
    team_players_names = [player['name'] for player in roster]
    team_players_status = [player['status'] for player in roster]

    return {team_name: {'ids': team_names_ids, 'names': team_players_names, 'status': team_players_status}}


def fetch_teams_roster_ids(sc, lg, datetime_obj, league_id, fetch_k_teams=12):
    """Fetch team roster for week and day. Returns dict with team name as key and list of players ids as value."""
    url = f'https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/teams'
    kwargs = {'params': {'format': 'json'}, 'allow_redirects': True}
    with sc.session as s:
        res = s.request('GET', url, **kwargs)
        teams = list(res.json()['fantasy_content']['league'][1]['teams'].values())
        teams_names_keys = {team['team'][0][2]['name']: team['team'][0][0]['team_key']
                            for team in teams[:fetch_k_teams] if isinstance(team, dict)}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(fetch_roster_data_concurrently, lg, team_key, team_name, datetime_obj)
                       for team_name, team_key in teams_names_keys.items()]
            results = [future.result() for future in futures]
            results = {team_name: team_dict for team_dict in results for team_name, team_dict in team_dict.items()}
        sc.session.close()

        return results


def get_teams_stats_date_range(sc, lg, dates_list, league_id, plot=False):
    """ Fetch team stats for dates in dates_tuples. Returns pandas DataFrame with team stats of the sum of all dates. """

    numeric_cols = ['FGA', 'FGM', 'FTA', 'FTM', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO', 'games_played']
    teams_names = [team['name'] for team_id, team in lg.teams().items()]
    weekly_summarized_df = {team_name: [] for team_name in teams_names}

    for date in dates_list:
        print(f"starting for date {date}")
        teams_names_ids_status = fetch_teams_roster_ids(sc, lg, datetime_obj=date, league_id=league_id)
        daily_all_players_ids = [player_id
                                 for team_name, players_ids_statutes in teams_names_ids_status.items()
                                 for player_id in players_ids_statutes['ids'][:10]]

        teams_daily_dfs = fetch_daily_data(sc, daily_all_players_ids, date=date)
        numeric_df = teams_daily_dfs.apply(pd.to_numeric, errors='coerce')
        for team_name, players_ids_statutes in teams_names_ids_status.items():
            specific_team_daily_df = numeric_df.loc[numeric_df['player_id'].isin(players_ids_statutes['ids'][:10])][numeric_cols]
            weekly_summarized_df[team_name].append(specific_team_daily_df)

    for team_name in teams_names:
        team_weekly_sum_df = pd.concat(weekly_summarized_df[team_name]).groupby(level=0).sum().fillna(0)

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


def fetch_daily_data(sc, players_ids, date=datetime.date.today()):
    """Fetch daily data for players in players_ids list for date. Returns pandas DataFrame with players stats."""
    '''set the list of players ids as lists of max 24 ids each'''
    players_ids_lists = [players_ids[i:i + 24] for i in range(0, len(players_ids), 24)]
    final_dict = {}
    for players_ids in players_ids_lists:
        url_base = 'https://fantasysports.yahooapis.com/fantasy/v2/players;player_keys='
        url_end = '/stats;type=date;date='
        url = url_base + ','.join([f"nba.p.{id}" for id in players_ids]) + url_end + date.strftime('%Y-%m-%d')
        kwargs = {'params': {'format': 'json'}, 'allow_redirects': True}
        with sc.session as s:
            res = s.request('GET', url, **kwargs)
            j = res.json()
            players_dict = {}

            for player in [p for p in j['fantasy_content']['players'].values()]:
                if not isinstance(player, dict):
                    continue
                player_name = player['player'][0][2]['name']['full']
                player_id = player['player'][0][1]['player_id']
                player_stats_to_val = {stat['stat']['stat_id']: stat['stat']['value'] for stat in
                                       player['player'][1]['player_stats']['stats']}
                players_stats_cat = {convert_id_to_cat(stat_id): stat_val for stat_id, stat_val in
                                     player_stats_to_val.items()}
                try:
                    played_minutes = int(player['player'][1]['player_stats']['stats'][2]['stat']['value'])
                    players_stats_cat['games_played'] = 1 if played_minutes > 0 else 0
                except:
                    players_stats_cat['games_played'] = 0

                players_stats_cat.pop(None, None)
                players_stats_cat['player_id'] = player_id
                players_dict[player_name] = players_stats_cat

            final_dict.update(players_dict)
    sc.session.close()
    return pd.DataFrame(final_dict).T


def convert_id_to_cat(stat_id):
    """Convert stat id to category. Returns category name. expects stat_id to be string."""
    stat_id_to_category = {3: 'FGA', 4: 'FGM', 5: 'FG%', 6: 'FTA', 7: 'FTM', 8: 'FT%', 10: '3PTM', 12: 'PTS',
                           15: 'REB', 16: 'AST', 17: 'ST', 18: 'BLK', 19: 'TO', 9004003: 'FGM/FGA', 9007006: 'FTM/FTA'}

    return stat_id_to_category.get(int(stat_id), None)


def get_player_ranks(league):
    all_ranks = {}
    rank_start = 0
    while rank_start < 150:
        ranked_players = league.yhandler.get(f"/league/{league.league_id}/players;sort=AR;start={rank_start}")
        player_dict = ranked_players['fantasy_content']['league'][1]['players']
        if player_dict == []:
            break
        ranks = {}
        for maybe_rank, player in player_dict.items():
            if maybe_rank == 'count':
                continue
            player_full_name = player['player'][0][2]['name']['full']
            ranks[player_full_name] = rank_start + int(maybe_rank) + 1

        all_ranks.update(ranks)
        rank_start += 25
    return all_ranks


def convert_date_to_week_day(date=datetime.datetime.today()):
    """Convert date to week and day. Returns tuple of week and day."""
    first_day = datetime.datetime(2023, 10, 23)
    week = (date - first_day).days // 7 + 1
    day = (date - first_day).days % 7 + 1

    return week, day


def fetch_current_week_league_schedule(week):
    url = "https://hashtagbasketball.com/advanced-nba-schedule-grid"
    response = requests.get(url)

    if response.status_code == 200:
        page_content = response.text
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        page_content = None

    soup = BeautifulSoup(page_content, 'html.parser')
    dates = soup.find_all('h4', class_='above-table-title pt-1 d-none d-sm-block')[0].text.split(' - ')
    start_date, end_date = [datetime.datetime.strptime(date, '%A %d %B %Y') for date in dates]
    table = soup.find(id=f'ContentPlaceHolder1_w{week}_GridView1')
    rows = table.find_all('tr')
    columns = [v.text.replace('\n', '') for v in rows[0].find_all('th')]
    df = pd.DataFrame(columns=columns)
    for i in range(1, len(rows)):
        tds = rows[i].find_all('td')
        if len(tds) == 4:
            values = [tds[0].text, tds[1].text, tds[2].text, tds[3].text]
        else:
            values = [td.text for td in tds]
        if values[0] not in ['Team', '# Games Played']:
            df.loc[len(df)] = values

    df.drop(columns=df.columns[-2:], inplace=True)
    df.replace('\xa0', '-', inplace=True)
    df['Games'] = df['Games'].astype(int)
    df.columns = ['Team', 'Games'] + [start_date + datetime.timedelta(days=i) for i in range(df.shape[1] - 2)]

    today_date = datetime.datetime.combine(datetime.datetime.now(tz=pytz.timezone('US/Eastern')), datetime.time())
    columns_passed = (today_date - start_date).days
    df = df[['Team', 'Games'] + list(df.columns[2 + columns_passed:])]
    df['Games'] = df[df.columns[2:]].ne('-').sum(axis=1)

    return df


def get_all_players_details(sc, lg, teams_schedule, datetime_obj, league_id):
    """
    Fetch all players details for datetime_obj. Returns pandas DataFrame with players stats and team schedule.
    used for calculating players stats for the week, and getting the team schedule for the week.
    """
    league_rosters = fetch_teams_roster_ids(sc, lg, datetime_obj=datetime_obj, league_id=league_id)
    all_ids = [player_id for team_name, players_ids_statutes in league_rosters.items() for player_id in
               players_ids_statutes['ids']]
    players_full_data = lg.player_details(all_ids)
    players_avg_stats_dict = {
        player_obj['name']['full']: {convert_id_to_cat(stat['stat']['stat_id']): stat['stat']['value']
                                     for stat in player_obj['player_stats']['stats']}

        for player_obj in players_full_data if isinstance(player_obj, dict)}
    players_name_to_team = {player_obj['name']['full']: player_obj['editorial_team_full_name']
                            for player_obj in players_full_data if isinstance(player_obj, dict)}

    players_name_to_team = {player_name: team_name if team_name != 'LA Clippers' else 'Los Angeles Clippers' for
                            player_name, team_name in players_name_to_team.items()}
    players_avg_stats_df = pd.DataFrame(players_avg_stats_dict).T
    players_avg_stats_df['Team'] = players_avg_stats_df.index.map(players_name_to_team)

    teams_schedule.set_index('Team', inplace=True)
    return players_avg_stats_df.merge(teams_schedule, left_on='Team', right_index=True)


def get_all_time_matchups_differential(sc):
    gm = yfa.Game(sc, 'nba')
    leagues_ids = gm.league_ids(year=2022) + gm.league_ids(year=2023)
    matchups_results = []
    for league_id in leagues_ids:
        if league_id == '428.l.114976':
            '''skip dor's league'''
            continue
        lg = gm.to_league(league_id)
        num_of_weeks = int(lg.settings()['current_week'])
        for week in range(1, num_of_weeks + 1):
            lg_matchups = lg.matchups(week=week)
            for i, matchup in lg_matchups['fantasy_content']['league'][1]['scoreboard']['0']['matchups'].items():
                if i == 'count':
                    continue
                team_a_stats_obj = matchup['matchup']['0']['teams']['0']['team'][1]['team_stats']['stats']
                team_b_stats_obj = matchup['matchup']['0']['teams']['1']['team'][1]['team_stats']['stats']

                team_a_stats = {convert_id_to_cat(stat['stat']['stat_id']): stat['stat']['value'] for stat in
                                team_a_stats_obj}
                team_b_stats = {convert_id_to_cat(stat['stat']['stat_id']): stat['stat']['value'] for stat in
                                team_b_stats_obj}
                team_a_stats['match_id'] = f'{i}_{week}_{league_id}'
                team_b_stats['match_id'] = f'{i}_{week}_{league_id}'

                '''sort the stats by category'''
                team_a_stats = {k: v for k, v in sorted(team_a_stats.items(), key=lambda item: item[0])}
                team_b_stats = {k: v for k, v in sorted(team_b_stats.items(), key=lambda item: item[0])}

                matchups_results.append(team_a_stats)
                matchups_results.append(team_b_stats)

    df = pd.DataFrame(matchups_results)
    df[['FGM', 'FGA']] = df['FGM/FGA'].str.split('/', expand=True)
    df[['FTM', 'FTA']] = df['FTM/FTA'].str.split('/', expand=True)
    df.drop(columns=['FGM/FGA', 'FTM/FTA', 'FG%', 'FT%'], inplace=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    df = df.groupby('match_id').apply(lambda x: abs(x.iloc[0] - x.iloc[1]))

    with open('../local_db/all_time_matchups_differential.pkl', 'wb') as f:
        pickle.dump(df, f)


if __name__ == '__main__':
    league_name = "Sheniuk"
    sc, lg, league_id, current_week, start_date, end_date = init_configuration(league_name, week=6, from_file='../oauth2.json')
    get_all_time_matchups_differential(sc)
    teams_schedule = fetch_current_week_league_schedule()
    datetime_obj = datetime.datetime.combine(start_date, datetime.time())
    get_all_players_details(sc, lg, teams_schedule, datetime_obj, league_id)



