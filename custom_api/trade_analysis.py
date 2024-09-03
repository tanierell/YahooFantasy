from utils import (init_configuration, init_db_config, fetch_roster_ids_by_dates, load_players_avg_by_date)

import datetime, pytz, logging, pickle
import pandas as pd
from scipy.stats import norm
import matplotlib.pyplot as plt


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


def plot_trade_summary(trade_summarizer, num_teams):
    """
        trade_summarizer is a dict with keys 'before' and 'after', each with keys 'avg', 'ranks', 'prob'.
        Each of these is a dataframe with the relevant data.
    """
    generate_row_colors_probs = lambda row: [plt.cm.RdYlGn(val) for val in row]
    generate_row_colors_ranks = lambda num_teams, row: [plt.cm.RdYlGn(1 - (rank - 1) / (num_teams - 1)) for rank in row]

    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(12, 12))
    fig.subplots_adjust(hspace=0.05)
    row_titles = ['Average', 'Ranks', 'Probability']

    for time in ['before', 'after']:
        col = 0 if time == 'before' else 1

        for key in ['avg', 'ranks']:
            row = 0 if key == 'avg' else 1
            temp_df = trade_summarizer[time][key]
            if key == 'avg':
                temp_df['FG%'] = temp_df['FGM'] / temp_df['FGA']
                temp_df['FT%'] = temp_df['FTM'] / temp_df['FTA']
                temp_df.drop(columns=['FGM', 'FGA', 'FTM', 'FTA'], inplace=True)
                temp_df = temp_df.round(2)
            if key == 'ranks':
                temp_df = temp_df.astype(int)

            ranks_colors = [generate_row_colors_ranks(num_teams, row) for _, row in
                            trade_summarizer[time]["ranks"].iterrows()]
            table = pd.plotting.table(axes[row, col], temp_df, loc='center', cellColours=ranks_colors, cellLoc='center')
            table.auto_set_column_width(col=list(range(len(temp_df.columns))))
            table.auto_set_font_size(True)
            table.scale(1, 1.2)

            axes[row, col].set_title(f"{row_titles[key == 'ranks']} {time.capitalize()}")

        prob_colors = [generate_row_colors_probs(row) for _, row in trade_summarizer[time]['prob'].iterrows()]
        temp_df = trade_summarizer[time]['prob'].copy()
        temp_df = temp_df.round(2)
        table = pd.plotting.table(axes[2, col], temp_df, loc='center', cellColours=prob_colors, cellLoc='center')
        axes[2, col].set_title(f'{row_titles[2]} {time.capitalize()}')

        table.auto_set_column_width(col=list(range(len(temp_df.columns))))
        table.auto_set_font_size(True)
        table.scale(1, 1.2)

    for ax in axes.flatten():
        ax.axis('off')

    plt.tight_layout()
    plt.savefig(f'../trade_summary.png')
    plt.show()


def analyze_given_situation(team_names_averages):
    stats_cols = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
    league_avg_by_team = pd.DataFrame(columns=stats_cols)

    # kuminga = team_names_averages['TheRealTani'].loc['Jonathan Kuminga']
    # jaren_jackson = team_names_averages['LeTippex'].loc['Jaren Jackson Jr.']
    # dejunte_murray = team_names_averages['BCMeidan'].loc['Dejounte Murray']
    #
    # tani_team = team_names_averages['TheRealTani'].copy()
    # tani_team.drop(index=['Shai Gilgeous-Alexander'], inplace=True)
    # tani_team.drop(index=['Jonathan Kuminga'], inplace=True)
    # tani_team.loc['Jaren Jackson Jr.'] = jaren_jackson
    # tani_team.loc['Dejounte Murray'] = dejunte_murray
    # team_names_averages['new_team'] = tani_team
    # league_avg_by_team.loc[TheRealTani] += list(team_names_averages['LeTippex'].loc['Jaren Jackson Jr.'])

    for team_name, df in team_names_averages.items():
        league_avg_by_team.loc[team_name] = list(df.sum(axis=0))

    league_avg_by_team['TO'] *= -1
    league_places_per_cat = league_avg_by_team.copy()
    league_places_per_cat['FG%'] = league_places_per_cat['FGM'] / league_places_per_cat['FGA']
    league_places_per_cat['FT%'] = league_places_per_cat['FTM'] / league_places_per_cat['FTA']
    league_places_per_cat.drop(columns=['FGM', 'FGA', 'FTM', 'FTA'], inplace=True)
    league_places_per_cat = league_places_per_cat.rank(axis=0, ascending=False)

    league_avg_by_team['TO'] *= -1
    df = league_avg_by_team.copy()
    df['FG%'] = df['FGM'] / df['FGA']
    df['FT%'] = df['FTM'] / df['FTA']
    df.drop(columns=['FGM', 'FGA', 'FTM', 'FTA'], inplace=True)
    means = df.mean()
    stds = df.std()

    prob_df = df.apply(lambda x: norm.cdf(x, means[x.name], stds[x.name]))
    prob_df['TO'] = 1 - prob_df['TO']
    league_avg_by_team.loc['mean'] = league_avg_by_team.mean(axis=0)
    league_avg_by_team.loc['std'] = league_avg_by_team.std(axis=0)

    return league_avg_by_team, league_places_per_cat, prob_df


def analyze_trade(engine, team_names_averages=None, use_saved=True):
    league_name = "Ootan" if input(f"Choose league:\n1: Ootan, 2: Sheniuk") == '1' else "Sheniuk"
    if use_saved:
        team_names_averages = pickle.load(open(f'../{league_name}-teams_names_averages.pkl', 'rb'))

    lists_of_ids = [df.index.tolist() for name, df in team_names_averages.items()]
    all_ids = [item for sublist in lists_of_ids for item in sublist]
    sql_query = f"SELECT * FROM players_season_totals WHERE yahoo_id IN {tuple(all_ids)};"
    all_players_info = pd.read_sql_query(sql_query, engine, index_col='yahoo_id')[['full_name']]
    for team_name, df in team_names_averages.items():
        df.index = all_players_info.loc[df.index]['full_name']
        team_names_averages[team_name] = df

    while 1:
        init_print = [f"{i}: {name}" for i, name in enumerate(team_names_averages.keys())]
        print("\n".join(init_print))
        team_a, team_b = input("Enter team numbers to trade (separated by comma): ").split(',')

        if int(team_a) >= len(team_names_averages) or int(team_b) >= len(team_names_averages):
            print("Invalid team number")
            continue
        team_names_averages_copy = team_names_averages.copy()
        trade_summarizer = {"before": {}, "after": {}}

        team_a_name = list(team_names_averages.keys())[int(team_a)]
        team_b_name = list(team_names_averages.keys())[int(team_b)]
        team_a_players = team_names_averages[team_a_name].index.tolist()
        team_b_players = team_names_averages[team_b_name].index.tolist()

        league_avg, league_ranks, league_prob = analyze_given_situation(team_names_averages)

        trade_summarizer["before"]["avg"] = league_avg.loc[[team_a_name, team_b_name]]
        trade_summarizer["before"]["ranks"] = league_ranks.loc[[team_a_name, team_b_name]]
        trade_summarizer["before"]["prob"] = league_prob.loc[[team_a_name, team_b_name]]

        team_a_ps_print = [f"{i}: {name}" for i, name in enumerate(team_a_players)]
        team_b_ps_print = [f"{i}: {name}" for i, name in enumerate(team_b_players)]
        print(f"Team {team_a_name} players:\n")
        print("\n".join(team_a_ps_print))
        team_a_traded_players = input(f"Enter team A traded players' index (separated by comma): ")
        print(f"Team {team_b_name} players:\n")
        print("\n".join(team_b_ps_print))
        team_b_traded_players = input(f"Enter team B traded players' index (separated by comma): ")
        team_a_traded_players = [team_a_players[int(i)] for i in team_a_traded_players.split(',')]
        team_b_traded_players = [team_b_players[int(i)] for i in team_b_traded_players.split(',')]

        fetched_stats_traded_players_a = team_names_averages_copy[team_a_name].loc[team_a_traded_players]
        fetched_stats_traded_players_b = team_names_averages_copy[team_b_name].loc[team_b_traded_players]

        team_names_averages_copy[team_a_name] = team_names_averages_copy[team_a_name].drop(index=team_a_traded_players)
        team_names_averages_copy[team_b_name] = team_names_averages_copy[team_b_name].drop(index=team_b_traded_players)

        team_names_averages_copy[team_a_name] = pd.concat([team_names_averages_copy[team_a_name], fetched_stats_traded_players_b])
        team_names_averages_copy[team_b_name] = pd.concat([team_names_averages_copy[team_b_name], fetched_stats_traded_players_a])

        league_avg, league_ranks, league_prob = analyze_given_situation(team_names_averages_copy)
        trade_summarizer["after"]["avg"] = league_avg.loc[[team_a_name, team_b_name]]
        trade_summarizer["after"]["ranks"] = league_ranks.loc[[team_a_name, team_b_name]]
        trade_summarizer["after"]["prob"] = league_prob.loc[[team_a_name, team_b_name]]

        plot_trade_summary(trade_summarizer.copy(), len(team_names_averages))

        print("Continue? (y/n)")
        if input() == 'n':
            break


if __name__ == '__main__':
    engine = init_db_config(path_to_db_config='../config.ini')
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)

    analyze_trade(engine, use_saved=True)
    week = 18
    players_stats_method = 'custom_dates'
    for league_name in ["Sheniuk", "Ootan"]:
        sc, _, league_id, _, _, _ = init_configuration(league_name=league_name, week=week, from_file="../oauth2.json")

        top_players_ranks = get_players_current_ratings(sc, league_id, top_k=200)
        top_p_ids = top_players_ranks.index.tolist()
        players_totals_query = f"SELECT * FROM players_season_totals WHERE yahoo_id IN {tuple(top_p_ids)};"
        players_custom_query = f"SELECT * FROM players_history_stats_daily WHERE yahoo_id IN {tuple(top_p_ids)};"

        query = players_custom_query if players_stats_method == 'custom_dates' else players_totals_query
        full_players_totals = pd.read_sql_query(query, engine, index_col='yahoo_id')

        full_players_avg = load_players_avg_by_date(full_players_totals, players_stats_method=players_stats_method)

        ect_time = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
        today_date = datetime.datetime.combine(ect_time, datetime.time())
        rosters_data = fetch_roster_ids_by_dates(sc=sc, datetime_objects=[today_date], league_id=league_id)

        teams_names_averages = {}
        stats_cols = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
        league_avg_by_team = pd.DataFrame(columns=stats_cols)
        for team_name, roster_info_df in rosters_data.groupby('team_name'):
            players_names = roster_info_df['full_name'].tolist()
            players_status = roster_info_df['status'].tolist()
            players_ids = roster_info_df['yahoo_id'].tolist()
            players_positions = roster_info_df['position'].tolist()

            cur_team_ranks = top_players_ranks.loc[top_players_ranks.index.isin(players_ids)].sort_values(by='rank')
            included_players = [name for name, status in zip(players_names, players_status)
                                if status != 'INJ' and name in cur_team_ranks.full_name.tolist()][:13]

            # included_players = [p_id for p_id, status in zip(players_ids, players_status) if p_id in cur_team_ranks.index]
            current_team_averages = full_players_avg[full_players_avg.full_name.isin(included_players)][stats_cols]
            teams_names_averages[team_name] = current_team_averages
            league_avg_by_team.loc[team_name] = list(current_team_averages.sum(axis=0))

        # league_avg_by_team, league_places_per_cat, prob_df = analyze_given_situation(teams_names_averages)
        #
        # """for each team, print the number of categories it is above each other team """
        # for team_name, team_avg in league_places_per_cat.iterrows():
        #     for other_team_name, other_team_avg in league_places_per_cat.iterrows():
        #         if team_name == other_team_name:
        #             continue
        #         print(f"{team_name} is above {other_team_name} in {sum(team_avg < other_team_avg)} categories")

        with open(f'../{league_name}-teams_names_averages.pkl', 'wb') as f:
            pickle.dump(teams_names_averages, f)
        # league_avg_by_team.to_csv(f'../league_avg_by_team.csv')
        # league_places_per_cat.to_csv(f'../league_places_per_cat.csv')
        # prob_df.to_csv(f'../prob_df.csv')
