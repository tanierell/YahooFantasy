from utils import init_configuration, convert_id_to_cat
import pandas as pd
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa


def get_week_results_per_team(lg, week):
    matchups = list(lg.matchups(week=week)['fantasy_content']['league'][1]['scoreboard']['0']['matchups'].values())
    team_weekly_stats = {}
    for matchup in [x for x in matchups if isinstance(x, dict)]:
        teams = matchup['matchup']['0']['teams'].values()
        for team in [x for x in teams if isinstance(x, dict)]:
            team_name = team['team'][0][2]['name']
            team_stats = team['team'][1]['team_stats']['stats']
            team_weekly_stats[team_name] = {stat['stat']['stat_id']: stat['stat']['value'] for stat in team_stats}

    team_weekly_cat = {team: {convert_id_to_cat(stat_id): val for stat_id, val in stats.items()}
                       for team, stats in team_weekly_stats.items()}

    df = pd.DataFrame.from_dict(team_weekly_cat, orient='index')
    df[['FGM', 'FGA']] = df['FGM/FGA'].str.split('/', expand=True)
    df[['FGM', 'FGA']] = df[['FGM', 'FGA']].apply(pd.to_numeric, errors='coerce')
    '''drop teams where FGA is < 100 and FTM/FTA is < 50'''
    df['FG%'] = df['FGM'] / df['FGA']
    df[['FTM', 'FTA']] = df['FTM/FTA'].str.split('/', expand=True)
    df[['FTM', 'FTA']] = df[['FTM', 'FTA']].apply(pd.to_numeric, errors='coerce')
    df['FT%'] = df['FTM'] / df['FTA']
    new_df = df[df['FGA'] > 100]
    new_df = new_df[new_df['FTA'] > 50]
    if len(new_df) < len(df):
        print(f"dropped {len(df) - len(new_df)} teams")
    new_df.drop(['FGM/FGA', 'FTM/FTA', 'FGM', 'FGA', 'FTM', 'FTA'], axis=1, inplace=True)
    new_df = new_df.apply(pd.to_numeric, errors='coerce')

    return new_df


if __name__ == '__main__':
    # league_name = "Ootan"
    league_name = "Sheniuk"
    sc, lg, league_id, current_week, start_date, end_date = init_configuration(league_name=league_name, week=10, from_file="../oauth2.json")
    sc = OAuth2(None, None, from_file="../oauth2.json")
    gm = yfa.Game(sc, 'nba')
    leagues = gm.league_ids()

    measured_categories = ["FG%", "FT%", "3PTM", "PTS", "REB", "AST", "ST", "BLK", "TO"]
    history_best_by_category = pd.DataFrame(columns=measured_categories)
    history_best_by_category.loc["Best Team"] = [None for _ in range(len(measured_categories))]
    history_best_by_category.loc["Record"] = [0 for _ in range(len(measured_categories))]
    history_best_by_category.loc["When"] = [None for _ in range(len(measured_categories))]

    history_worst_by_category = pd.DataFrame(columns=measured_categories)
    history_worst_by_category.loc["Worst Team"] = [None for _ in range(len(measured_categories))]
    history_worst_by_category.loc["Record"] = [100000 for _ in range(len(measured_categories))]
    history_worst_by_category.loc["When"] = [None for _ in range(len(measured_categories))]

    for league_id in ['418.l.73059', '428.l.2540']:
        lg = gm.to_league(league_id)
        lg_current_week = lg.current_week()
        year = "2023" if league_id == '418.l.73059' else "2024"
        for week in range(1, lg_current_week + 1 if league_id == '418.l.73059' else lg_current_week):
            current_week_results = get_week_results_per_team(lg, week)
            for category in measured_categories:
                best_team = current_week_results[category].idxmax()
                best_value = current_week_results[category].max()
                worst_team = current_week_results[category].idxmin()
                worst_value = current_week_results[category].min()

                if best_value > history_best_by_category.at["Record", category]:
                    history_best_by_category.at["Best Team", category] = best_team
                    history_best_by_category.at["Record", category] = best_value
                    history_best_by_category.at["When", category] = f"Year {year} Week {week}"

                if worst_value < history_worst_by_category.at["Record", category]:
                    history_worst_by_category.at["Worst Team", category] = worst_team
                    history_worst_by_category.at["Record", category] = worst_value
                    history_worst_by_category.at["When", category] = f"Year {year} Week {week}"

    best_to = history_best_by_category["TO"]
    worst_to = history_worst_by_category["TO"]
    history_best_by_category["TO"] = worst_to.values
    history_worst_by_category["TO"] = best_to.values
    history_best_by_category = history_best_by_category.round(3)
    history_worst_by_category = history_worst_by_category.round(3)
    all_time_records = {"Best": history_best_by_category, "Worst": history_worst_by_category}

    '''convert to txt as follows: fors each category print best and worst team and when it happened'''
    with open("sheniuk_all_time_records.txt", "w") as f:
        for category in all_time_records["Best"].columns:
            f.write(f"Category: {category}\n")
            f.write(f"\tBest Team: {all_time_records['Best'].at['Best Team', category]}, \tRecord: {round(all_time_records['Best'].at['Record', category], 3)}, \tWhen: {all_time_records['Best'].at['When', category]}\n")
            f.write(f"\tWorst Team: {all_time_records['Worst'].at['Worst Team', category]}, \tRecord: {round(all_time_records['Worst'].at['Record', category], 3)}, \tWhen: {all_time_records['Worst'].at['When', category]}\n")
            f.write("\n- - - - - - - - - - - - \n")
    # for category in all_time_records["Best"].columns:
    #     print(f"Category: {category}")
    #     print(f"\tBest Team: {all_time_records['Best'].at['Best Team', category]}, \tRecord: {all_time_records['Best'].at['Record', category]}, \tWhen: {all_time_records['Best'].at['When', category]}")
    #     print(f"\tWorst Team: {all_time_records['Worst'].at['Worst Team', category]}, \tRecord: {all_time_records['Worst'].at['Record', category]}, \tWhen: {all_time_records['Worst'].at['When', category]}")
    #     print("\n- - - - - - - - - - - - \n")




