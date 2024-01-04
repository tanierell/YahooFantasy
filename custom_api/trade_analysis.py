from utils import (init_configuration, init_db_config, fetch_teams_roster_ids)

import pickle, datetime, pytz, logging
import pandas as pd
from scipy.stats import norm
import concurrent.futures


def get_players_current_ratings(sc, league_id, top_k):
    top_players_ranks = []
    top_players_ids = []
    kwargs = {'params': {'format': 'json'}, 'allow_redirects': True}
    with sc.session as s:
        for start in range(0, top_k, 25):
            url = f'https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/players;status=T;sort=OR;start={start}'
            res = s.request('GET', url, **kwargs).json()['fantasy_content']['league'][1]['players']
            if not isinstance(res, dict):
                break
            top_players_ids += [fa_obj['player'][0][1]['player_id'] for i, fa_obj in res.items() if i != 'count']
            top_players_ranks += [fa_obj['player'][0][2]['name']['full'] for i, fa_obj in res.items() if i != 'count']

    s.close()
    ranks = list(range(1, len(top_players_ranks) + 1))
    data = [(rank, p_name) for rank, p_name in zip(ranks, top_players_ranks)]
    top_p_df = pd.DataFrame(index=top_players_ids, columns=['rank', 'full_name'], data=data)

    return top_p_df


if __name__ == '__main__':
    engine = init_db_config(path_to_db_config='../postgreSQL_init/config.ini')

    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    # league_name = "Ootan"
    league_name = "Sheniuk"
    week = 11
    sc, lg, league_id, current_week, start_date, end_date = init_configuration(league_name=league_name, week=week, from_file="../oauth2.json")

    top_players_ranks = get_players_current_ratings(sc, league_id, top_k=200)
    top_p_ids = top_players_ranks.index.tolist()
    full_players_totals = pd.read_sql_query(f"SELECT * FROM players_season_totals WHERE yahoo_id IN {tuple(top_p_ids)};",
                                            engine, index_col='yahoo_id')
    stats_cols = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
    full_players_totals[stats_cols] = full_players_totals[stats_cols].div(full_players_totals['GP'], axis=0)
    full_players_avg = full_players_totals[['full_name'] + stats_cols]

    ect_time = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
    today_date = datetime.datetime.combine(ect_time, datetime.time())
    rosters_data = fetch_teams_roster_ids(sc, lg, datetime_obj=today_date, league_id=league_id)

    teams_names_averages = {}
    league_avg_by_team = pd.DataFrame(columns=stats_cols)
    for team_name, names_ids_statutes in rosters_data.items():
        players_names = names_ids_statutes['names']
        players_status = names_ids_statutes['status']
        players_ids = [str(p_id) for p_id in names_ids_statutes['ids']]
        cur_team_ranks = top_players_ranks.loc[top_players_ranks.index.isin(players_ids)].sort_values(by='rank').iloc[:13]

        # included_players = [name for name, status in zip(players_names, players_status)
        #                     if status != 'INJ' and name in current_team_players_ranks.index]

        included_players = [p_id for p_id, status in zip(players_ids, players_status) if p_id in cur_team_ranks.index]
        current_team_averages = full_players_avg[full_players_avg.index.isin(included_players)][stats_cols]
        teams_names_averages[team_name] = current_team_averages
        league_avg_by_team.loc[team_name] = list(current_team_averages.sum(axis=0))

    league_avg_by_team['TO'] *= -1
    league_places_by_avg = league_avg_by_team.copy()
    league_places_by_avg['FG%'] = league_places_by_avg['FGM'] / league_places_by_avg['FGA']
    league_places_by_avg['FT%'] = league_places_by_avg['FTM'] / league_places_by_avg['FTA']
    league_places_by_avg.drop(columns=['FGM', 'FGA', 'FTM', 'FTA'], inplace=True)
    league_places_by_avg = league_places_by_avg.rank(axis=0, ascending=False)

    """for each team, print the number of categories it is above each other team """
    for team_name, team_avg in league_places_by_avg.iterrows():
        for other_team_name, other_team_avg in league_places_by_avg.iterrows():
            if team_name == other_team_name:
                continue
            print(f"{team_name} is above {other_team_name} in {sum(team_avg < other_team_avg)} categories")

    league_avg_by_team['TO'] *= -1
    df = league_avg_by_team.copy()
    df['FG%'] = df['FGM'] / df['FGA']
    df['FT%'] = df['FTM'] / df['FTA']
    df.drop(columns=['FGM', 'FGA', 'FTM', 'FTA'], inplace=True)
    means = df.mean()
    stds = df.std()

    prob_df = df.apply(lambda x: 1 - norm.cdf(x, means[x.name], stds[x.name]))

    league_avg_by_team.loc['mean'] = league_avg_by_team.mean(axis=0)
    league_avg_by_team.loc['std'] = league_avg_by_team.std(axis=0)

    print(teams_names_averages)