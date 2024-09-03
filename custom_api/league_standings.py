import pandas as pd
import matplotlib.pyplot as plt

from utils import init_configuration


def get_updated_league_standings(lg, week, league_name):
    lg_standings_obj = lg.standings()
    matchups = list(lg.matchups(week=week)['fantasy_content']['league'][1]['scoreboard']['0']['matchups'].values())
    team_weekly_w_l_t = {}
    for matchup in [x for x in matchups if isinstance(x, dict)]:
        stats_winner = ['None' if 'is_tied' in stat['stat_winner'] else stat['stat_winner']['winner_team_key']
                        for stat in matchup['matchup']['stat_winners']]

        for team in [x for x in matchup['matchup']['0']['teams'].values() if isinstance(x, dict)]:
            team_name = team['team'][0][2]['name']
            '''count wind, losses and ties'''
            wins = stats_winner.count(team['team'][0][0]['team_key'])
            ties = stats_winner.count('None')
            losses = len(stats_winner) - wins - ties
            team_weekly_w_l_t[team_name] = {'wins': wins, 'losses': losses, 'ties': ties}

    lg_standings_df = pd.DataFrame(columns=['Team', 'Wins', 'Losses', 'Ties', 'Win%'])
    for team in lg_standings_obj:
        team_name = team['name']

        team_prev_wins = int(team['outcome_totals']['wins'])
        team_prev_losses = int(team['outcome_totals']['losses'])
        team_prev_ties = int(team['outcome_totals']['ties'])

        team_current_week_wins = team_weekly_w_l_t[team_name]['wins']
        team_current_week_losses = team_weekly_w_l_t[team_name]['losses']
        team_current_week_ties = team_weekly_w_l_t[team_name]['ties']

        team_total_wins = team_prev_wins + team_current_week_wins
        team_total_losses = team_prev_losses + team_current_week_losses
        team_total_ties = team_prev_ties + team_current_week_ties
        added_ties = team_total_ties / 2

        team_win_percentage = round(
            (team_total_wins + added_ties) / (team_total_wins + team_total_losses + team_total_ties), 3)
        lg_standings_df.loc[len(lg_standings_df)] = [team_name, team_total_wins, team_total_losses, team_total_ties,
                                                     team_win_percentage]

    lg_standings_df.sort_values(by=['Win%', 'Wins'], ascending=False, inplace=True)
    lg_standings_df.reset_index(inplace=True)
    lg_standings_df.rename(columns={'index': 'Previous Rank'}, inplace=True)
    lg_standings_df['Previous Rank'] += 1
    first_place_wins, first_place_losses = lg_standings_df.loc[0, ['Wins', 'Losses']]
    lg_standings_df['GB'] = ((first_place_wins - lg_standings_df['Wins']) +
                             (lg_standings_df['Losses'] - first_place_losses)) / 2
    lg_standings_df['Win%'] = lg_standings_df['Win%'].apply(lambda x: f"{x:.3f}")
    lg_standings_df["W-L-T"] = lg_standings_df.apply(lambda x: f"{x['Wins']}-{x['Losses']}-{x['Ties']}", axis=1)
    lg_standings_df = lg_standings_df[['Team', 'W-L-T', 'Win%', 'GB', 'Previous Rank']]
    lg_standings_df['Previous Rank'] = lg_standings_df['Previous Rank'].astype(int)
    lg_standings_df['GB'] = lg_standings_df['GB'].apply(lambda x: str(x) if x % 0.5 == 0 else f'{x:.0f}')
    lg_standings_df.index += 1

    fig = plt.figure(dpi=400)
    ax = fig.add_subplot(111)
    ax.xaxis.set_visible(False)

    table = pd.plotting.table(data=lg_standings_df, ax=ax, loc='center', cellLoc='center')
    ax.set_title(f"Standings - Week {week}")
    ax.set_axis_off()
    plt.savefig(f"outputs/Plots/{league_name}/{week}/standings_week_{week}.png", bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    league_name = "Sheniuk"
    # league_name = "Ootan"
    week = 14
    for league_name in ["Ootan", "Sheniuk"]:
        sc, lg, league_id, current_week, start_date, end_date = init_configuration(league_name=league_name, week=week,
                                                                                   from_file='../oauth2.json')

        get_updated_league_standings(lg, week, league_name)
