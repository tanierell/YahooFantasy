def fetch_GP_value(player_id):
    try:
        response = nba_endpoints.playerdashboardbyyearoveryear.PlayerDashboardByYearOverYear(player_id=player_id).get_data_frames()[0]
        gp_value = response['GP'].values[0]
        return gp_value
    except Exception as e:
        print(f"Error fetching GP value for player_id {player_id}: {str(e)}")
        return None


def process_player_id(player_id):
    gp_value = fetch_GP_value(player_id)
    return gp_value


def players_projections_current_week(sc, lg, league_id, rosters_data, league_matchups_status):
    teams_schedule = fetch_current_week_league_schedule()
    nba_api_df = pd.DataFrame(players,
                                       columns=['player_id', 'first_name', 'last_name', 'full_name', 'is_active'])
    nba_api_df = nba_api_df[nba_api_df['is_active'] == 1]
    nba_api_df = nba_api_df[['player_id', 'full_name']]
    nba_api_df['player_id'] = nba_api_df['player_id'].astype(str)

    all_players_details = get_all_players_details(sc, lg, teams_schedule, datetime_obj=end_date, league_id=league_id)
    projections_by_team = {}
    for team_name, names_ids_statutes in rosters_data.items():
        print(f"Fetching projections for team {team_name}")
        team_players_names = names_ids_statutes['names']
        team_nba_api_df = nba_api_df[nba_api_df['full_name'].isin(team_players_names)]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(process_player_id, team_nba_api_df['player_id']))
        team_nba_api_df['played_games'] = results

        players_names_to_status = {name: status for name, status in zip(team_players_names, names_ids_statutes['status'])}
        team_full_stats = all_players_details.loc[all_players_details.index.isin(team_players_names)]
        team_full_stats['status'] = team_full_stats.index.map(players_names_to_status)
        team_full_stats = team_full_stats[team_full_stats['status'] != 'INJ']
        team_full_stats = team_full_stats.merge(team_nba_api_df, left_index=True, right_on='full_name').set_index('full_name')

        fetched_needed_stats = team_full_stats[['FGM/FGA', 'FTM/FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']]
        fetched_needed_stats.loc[:, ('FGM', 'FGA')] = fetched_needed_stats['FGM/FGA'].str.split('/', expand=True)
        fetched_needed_stats.loc[:, ('FTM', 'FTA')] = fetched_needed_stats['FTM/FTA'].str.split('/', expand=True)

        fetched_needed_stats.drop(columns=['FGM/FGA', 'FTM/FTA'], inplace=True)
        fetched_needed_stats = fetched_needed_stats.astype(float)

        fetched_needed_stats = fetched_needed_stats.div(team_full_stats['played_games'], axis=0)
        fetched_needed_stats = fetched_needed_stats.mul(team_full_stats['played_games'], axis=0)

        fetched_needed_stats.fillna(0, inplace=True)
        fetched_needed_stats = fetched_needed_stats[~(fetched_needed_stats == 0).all(axis=1)]

        fetched_needed_stats['FG%'] = fetched_needed_stats['FGM'] / fetched_needed_stats['FGA']
        fetched_needed_stats['FT%'] = fetched_needed_stats['FTM'] / fetched_needed_stats['FTA']
        fetched_needed_stats.drop(columns=['FGM', 'FGA', 'FTM', 'FTA'], inplace=True)

        projections_by_team[team_name] = fetched_needed_stats

    return projections_by_team



def fetch_player_schedule_concurrent(player_id, player_name, end_date):
    player_prev_schedule = nba_endpoints.playergamelog.PlayerGameLog(player_id=player_id).get_data_frames()[0]
    player_next_schedule = nba_endpoints.playernextngames.PlayerNextNGames(player_id=player_id).get_data_frames()[0]
    player_season_average_obj = nba_endpoints.playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(
        player_id=player_id,
        season='2023-24',
        per_mode_detailed='PerGame').data_sets[0].data

    if len(player_prev_schedule) == 0:
        print(f"Could not fetch previous schedule for player {player_name} with id {player_id}")
        player_prev_schedule = pd.DataFrame(columns=['GAME_DATE', 'HOME_TEAM_ABBREVIATION', 'VISITOR_TEAM_ABBREVIATION'])
    else:
        split_criterion = lambda game: pd.Series(game.split(' @ ')[::-1]) if '@' in game else pd.Series(
            game.split(' vs. '))
        player_prev_schedule[['HOME_TEAM_ABBREVIATION', 'VISITOR_TEAM_ABBREVIATION']] = player_prev_schedule['MATCHUP'].apply(split_criterion)
        player_prev_schedule = player_prev_schedule[['GAME_DATE', 'HOME_TEAM_ABBREVIATION', 'VISITOR_TEAM_ABBREVIATION']]

    player_next_schedule = player_next_schedule[['GAME_DATE', 'HOME_TEAM_ABBREVIATION', 'VISITOR_TEAM_ABBREVIATION']]

    player_full_schedule = pd.concat([player_prev_schedule, player_next_schedule])
    player_full_schedule['GAME_DATE'] = pd.to_datetime(player_full_schedule['GAME_DATE'], format='%b %d, %Y')

    '''changing the start date to now, so we can use accumulation of the stats until now in US. convert end time to datetime object'''
    start_date = datetime.datetime.combine(datetime.datetime.now(tz=pytz.timezone('US/Eastern')), datetime.time())
    end_date = datetime.datetime.combine(end_date, datetime.time())

    player_schedule_by_dates = player_full_schedule[(player_full_schedule['GAME_DATE'] >= start_date) &
                                                    (player_full_schedule['GAME_DATE'] <= end_date)]

    needed_columns = ['FGM', 'FGA', 'FG3M', 'FTM', 'FTA', 'PTS', 'REB', 'AST',
                      'TOV', 'STL', 'BLK', 'player_id', 'player_name', 'number_of_games']
    if len(player_season_average_obj['data']) == 0:
        return {}
    else:
        player_season_avg_data = player_season_average_obj['data'][0] + [player_id, player_name, len(player_schedule_by_dates)]

    player_season_avg_columns = player_season_average_obj['headers'] + ['player_id', 'player_name', 'number_of_games']
    player_season_avg_dict = dict(zip(player_season_avg_columns, player_season_avg_data))

    return {k: player_season_avg_dict[k] for k in needed_columns}


def players_projections_by_dates_nba_api(league_matchups_status, team_name, names_ids_statutes, end_date):
    """
    used to get the projections of the players in the given dates, based on their season average
    """

    players_names = names_ids_statutes['names']
    players_name_to_status = {name: status for name, status in zip(players_names, names_ids_statutes['status'])}

    all_time_players_list = pickle.load(open('local_db/all_time_players_nba_api.pkl', 'rb'))
    all_time_players_df = pd.DataFrame(all_time_players_list,
                                       columns=['player_id', 'first_name', 'last_name', 'full_name', 'is_active'])[['player_id', 'full_name']]
    filtered_df = all_time_players_df[all_time_players_df['full_name'].str.contains('|'.join(players_names),
                                                                                    case=False, na=False)]
    player_ids_names = filtered_df.values.tolist()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_player_schedule_concurrent, player_id, player_name, end_date)
                   for player_id, player_name in player_ids_names]
        results = [future.result() for future in futures]
        time.sleep(0.6)

    stat_cols = ['FGM', 'FGA', 'FG3M', 'FTM', 'FTA', 'PTS', 'REB', 'AST', 'TOV', 'STL', 'BLK']
    players_season_average_df = pd.DataFrame(data=results,
                                             columns=stat_cols + ['player_id', 'player_name', 'number_of_games'])
    players_season_average_df.rename(columns={'TOV': 'TO', 'FG3M': '3PTM', 'STL': 'ST'}, inplace=True)
    players_season_average_df.set_index(['player_id', 'player_name'], inplace=True)
    num_games_vector = players_season_average_df['number_of_games']
    players_season_average_df.dropna(inplace=True)
    players_season_average_df.drop(columns=['number_of_games'], inplace=True)
    team_weekly_total = players_season_average_df.mul(num_games_vector, axis=0)

    team_weekly_total['status'] = team_weekly_total.index.get_level_values(1).map(players_name_to_status)
    team_weekly_total = team_weekly_total[team_weekly_total['status'] != 'INJ']

    team_accumulated_stats = league_matchups_status[team_name]
    '''add a row of the team's accumulated stats till today'''
    team_weekly_total.loc['Accumulated'] = [float(team_accumulated_stats[stat]) if stat in team_accumulated_stats else '-' for stat in team_weekly_total.columns]
    team_weekly_total.loc['Total'] = team_weekly_total.select_dtypes(include=[np.number]).sum(axis=0)
    team_weekly_total['FG%'] = team_weekly_total['FGM'] / team_weekly_total['FGA']
    team_weekly_total['FT%'] = team_weekly_total['FTM'] / team_weekly_total['FTA']

    team_weekly_total.rename(columns={'3PTM': '3PM', 'ST': 'STL'}, inplace=True)
    team_weekly_total.drop(columns=['FGM', 'FGA', 'FTM', 'FTA', 'status'], inplace=True)
    team_weekly_total = team_weekly_total[['FG%', 'FT%', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO']]
    team_weekly_total.fillna(0, inplace=True)
    team_weekly_total = team_weekly_total[~(team_weekly_total == 0).all(axis=1)]

    return team_weekly_total
