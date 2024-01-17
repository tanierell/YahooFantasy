import os
import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from utils import get_teams_stats_date_range, init_configuration, init_db_config


def distribution_of_played_games_by_team(sc, lg, league_id, engine, current_week=None, league_name="", plot=False):
    start_date, end_date = lg.week_date_range(current_week)
    start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time()) + datetime.timedelta(hours=2)
    weekly_dates = [start_date + datetime.timedelta(days=i) for i in range(7)]
    team_weakly_stats = get_teams_stats_date_range(sc=sc, engine=engine, dates_list=weekly_dates, league_id=league_id)
    draft_picks = lg.draft_results()
    draft_df = pd.DataFrame(draft_picks)
    draft_players_ids = draft_df['player_id'].astype(int).tolist()
    draft_players_names = [player_obj['name']['full'] for player_obj in lg.player_details(draft_players_ids)]
    teams_id_to_names = {team_id: team_obj['name'] for team_id, team_obj in lg.teams().items()}
    draft_df['team_name'] = draft_df['team_key'].map(teams_id_to_names)
    draft_df['player_name'] = draft_df['player_id'].map(dict(zip(draft_players_ids, draft_players_names)))
    draft_df = draft_df[['round', 'pick', 'team_name', 'player_name']]

    power_rank_by_team = {}
    for team_name in team_weakly_stats:
        merged_df = team_weakly_stats[team_name].merge(draft_df, how='left', right_on='player_name', left_index=True)
        merged_df = merged_df[['GP', 'round', 'player_name']].set_index('player_name')
        merged_df['round'].fillna(14, inplace=True)
        merged_df = merged_df[merged_df.index != 'Total']
        merged_df['power_rank'] = merged_df['GP'] / merged_df['round']
        merged_df.sort_values('power_rank', ascending=False, inplace=True)
        merged_df.loc['Total'] = merged_df.sum(axis=0)
        power_rank_by_team[team_name] = merged_df

    total_ranks = sum([power_rank_by_team[team_name].loc['Total', 'power_rank'] for team_name in power_rank_by_team])
    teams_normalizes_total = {team_name: power_rank_by_team[team_name].loc['Total', 'power_rank'] / total_ranks for team_name in power_rank_by_team}
    sorted_normalized_rank_df = pd.DataFrame.from_dict(teams_normalizes_total, orient='index', columns=['normalized_rank']).sort_values('normalized_rank', ascending=False)

    colors = sns.color_palette("cool", len(sorted_normalized_rank_df))
    sns.set(style="whitegrid")
    plt.figure(figsize=(8, 6))
    ax = sns.barplot(x=sorted_normalized_rank_df.index, y='normalized_rank', data=sorted_normalized_rank_df,
                     palette=colors)
    ax.set_title(f'Played Games Ranking - Week {current_week}')
    ax.set_ylabel('Normalized Rank')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tight_layout()
    if not os.path.exists(f'../outputs/Plots/{league_name}/{current_week}'):
        os.makedirs(f'../outputs/Plots/{league_name}/{current_week}')
    plt.savefig(f'../outputs/Plots/{league_name}/{current_week}/played_games_ranking.png', bbox_inches='tight')
    if plot:
        plt.show()


if __name__ == '__main__':
    league_name = "Sheniuk"
    sc, lg, league_id, current_week, start_date, end_date = init_configuration(league_name, week=12,
                                                                               from_file='../oauth2.json')
    engine = init_db_config('../config.ini')
    distribution_of_played_games_by_team(sc, lg, engine, current_week=current_week, league_name=league_name, plot=True)