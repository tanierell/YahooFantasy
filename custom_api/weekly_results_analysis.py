import os
import logging
import warnings
import pandas as pd
import matplotlib.pyplot as plt

from utils import convert_id_to_cat, init_configuration, init_db_config


def weekly_summary_by_matchup(lg, week, plot=True, league_name="", caller_extra_path=''):
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
    df['FG%'] = df['FGM'] / df['FGA']
    df[['FTM', 'FTA']] = df['FTM/FTA'].str.split('/', expand=True)
    df[['FTM', 'FTA']] = df[['FTM', 'FTA']].apply(pd.to_numeric, errors='coerce')
    df['FT%'] = df['FTM'] / df['FTA']
    df.drop(['FGM/FGA', 'FTM/FTA', 'FGM', 'FGA', 'FTM', 'FTA'], axis=1, inplace=True)
    df = df.apply(pd.to_numeric, errors='coerce')

    teams_names = list(df.index)
    scores_df = pd.DataFrame(index=teams_names, columns=teams_names)
    copied_df = df.copy()
    copied_df['TO'] *= -1
    for team1 in teams_names:
        for team2 in teams_names:
            if team1 == team2:
                scores_df.loc[team1, team2] = '-'  # Set diagonal elements to 0
            else:
                winning_cat = (copied_df.loc[team1] > copied_df.loc[team2]).sum()
                draw_cat = (copied_df.loc[team1] == copied_df.loc[team2]).sum()
                losing_cat = (copied_df.loc[team1] < copied_df.loc[team2]).sum()
                scores_df.loc[team1, team2] = f"{winning_cat}-{losing_cat}-{draw_cat}"
    summary = []

    for team in teams_names:
        won = []
        lost = []
        draws = []

        for opponent in teams_names:
            if team != opponent:
                score = scores_df.at[team, opponent]
                win, lose, draw = [int(x) for x in score.split('-')]
                if win > lose:
                    won.append((opponent, score))
                elif win < lose:
                    lost.append((opponent, score))
                else:
                    draws.append((opponent, score))
        summary.append((team, won, lost, draws))

    if not os.path.exists(caller_extra_path + f'outputs/Texts/{league_name}/{week}'):
        os.makedirs(caller_extra_path + f'outputs/Texts/{league_name}/{week}')

    with open(caller_extra_path + f'outputs/Texts/{league_name}/{week}/league_cross_matchups_summary.txt', 'w', encoding='utf-8') as file:
        for team, won, lost, draw in summary:
            file.write(f"{team}:\n")
            file.write("  Won:\n")
            for opponent, score in won:
                file.write(f"    {opponent}: {score}\n")
            file.write("  Lost:\n")
            for opponent, score in lost:
                file.write(f"    {opponent}: {score}\n")
            file.write("  Draw:\n")
            for opponent, score in draw:
                file.write(f"    {opponent}: {score}\n")
            file.write('\n')

    worst_team_by_cat = df.idxmin(axis=0)
    worst_value_by_cat = df.min(axis=0)
    worst_team_cat_value = pd.concat([worst_team_by_cat, worst_value_by_cat], axis=1).rename(columns={0: 'team', 1: 'value'})

    best_team_by_cat = df.idxmax(axis=0)
    best_value_by_cat = df.max(axis=0)
    best_team_cat_value = pd.concat([best_team_by_cat, best_value_by_cat], axis=1).rename(columns={0: 'team', 1: 'value'})

    '''switch TO category - since the more TO the worse'''
    temp_to = worst_team_cat_value.loc['TO']
    worst_team_cat_value.loc['TO'] = best_team_cat_value.loc['TO']
    best_team_cat_value.loc['TO'] = temp_to

    calculate_place = lambda category_values: category_values.rank(ascending=False).astype(int)
    temp_df = df.copy()
    temp_df['TO'] *= -1
    places_df = temp_df.apply(calculate_place, axis=0)
    average_places = places_df.mean(axis=1).round(2).sort_values(ascending=True)
    num_teams = len(average_places)

    generate_row_colors = lambda num_teams, row: [plt.cm.RdYlGn(1 - (team_rank - 1) / (num_teams - 1)) for team_rank in row]
    cell_colors = [generate_row_colors(num_teams, row) for _, row in places_df.iterrows()]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('off')

    the_table = pd.plotting.table(ax, places_df, loc='center', cellColours=cell_colors)
    plt.tight_layout()
    if not os.path.exists(caller_extra_path + f'outputs/Plots/{league_name}/{week}'):
        os.makedirs(caller_extra_path + f'outputs/Plots/{league_name}/{week}')

    plt.title(f"Teams places for each category - Week {week}")
    plt.savefig(caller_extra_path + f'outputs/Plots/{league_name}/{week}/weekly_teams_places.png', bbox_inches='tight')
    if plot:
        plt.show()

    average_place_summary_title = f"Average place for each category - Week {week}"
    avg_place_summary = average_place_summary_title + "\n\n\t" + "\n\t".join([f"{team} - {average_place}" for team, average_place in average_places.items()])
    with open(caller_extra_path + f'outputs/Texts/{league_name}/{week}/weekly_average_place.txt', 'w', encoding='utf-8') as f:
        f.write(avg_place_summary)

    plt.figure(figsize=(12, 10))
    for i, column in enumerate(df.columns):
        plt.subplot(3, 3, i+1)
        y_min = 0.9 * df[column].min()
        y_max = 1.5 * df[column].max()
        colors = ['red' if team == df[column].idxmin() else 'green' if team == df[column].idxmax() else 'blue' for
                  team in df.index]
        if column == "TO":
            colors = ['green' if team == df[column].idxmin() else 'red' if team == df[column].idxmax() else 'blue' for
                      team in df.index]
        for j, patch in enumerate(plt.bar(df.index, df[column], color=colors)):
            if "%" in column:
                plt.text(x=j, y=df[column][j] + 0.1, s=f"{df[column][j]:.2f}", ha='center', va='top', fontsize=6)
                plt.ylim(y_min, 1 if "FT" in column else y_max)
            else:
                plt.text(x=j, y=df[column][j] + 0.1 * y_max, s=df[column][j], ha='center', va='top', fontsize=6)
                plt.ylim(y_min, y_max)

        plt.xticks(rotation=45, ha='right', fontsize=8)
        plt.title(column)

    plt.suptitle(f"Managers Comparison - Week {week}", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    if not os.path.exists(caller_extra_path + f'outputs/Plots/{league_name}/{week}'):
        os.makedirs(caller_extra_path + f'outputs/Plots/{league_name}/{week}')
    plt.savefig(caller_extra_path + f'outputs/Plots/{league_name}/{week}/weekly_stats_my_manager.png',
                bbox_inches='tight')
    if plot:
        plt.show()

    textual_summary_title = f"Managers Comparison - Week {week}"
    '''summary looks like: Category - Worst team: value \n Category - Best team: value'''
    categorical_summary = ""
    for category in df.columns:
        categorical_summary += f"{category} \n\t --BEST-- {best_team_cat_value.loc[category]['team']}: {best_team_cat_value.loc[category]['value']}" \
                               f"\n\t --WORST-- {worst_team_cat_value.loc[category]['team']}: {worst_team_cat_value.loc[category]['value']}\n\n"

    textual_summary = textual_summary_title + "\n\n" + categorical_summary
    with open(caller_extra_path + f'outputs/Texts/{league_name}/{week}/weekly_best_worst_category.txt', 'w', encoding='utf-8') as f:
        f.write(textual_summary)


if __name__ == '__main__':
    engine = init_db_config(path_to_db_config='../config.ini')

    warnings.filterwarnings('ignore')
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)

    week = 12
    for league_name in ["Ootan", "Sheniuk"]:
        sc, lg, league_id, current_week, _, end_date = init_configuration(league_name=league_name, week=week,
                                                                          from_file='../oauth2.json')

        weekly_summary_by_matchup(lg, week=current_week, plot=False, league_name=league_name, caller_extra_path='../')