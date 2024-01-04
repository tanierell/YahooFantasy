import os
import pytz
import logging
import datetime
import warnings

from utils import init_configuration, init_db_config

from custom_api.weekly_projections import weekly_matchups_projections
from custom_api.games_amount_power_rank import distribution_of_played_games_by_team
from custom_api.FA_analysis import best_FA_pickup
from custom_api.weekly_results_analysis import weekly_summary_by_matchup

oauth_logger = logging.getLogger('yahoo_oauth')
oauth_logger.disabled = True


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)

    engine = init_db_config(path_to_db_config='postgreSQL_init/config.ini')

    for league_name in ["Ootan", "Sheniuk"]:
        print(f"League: {league_name}")
        week = 11
        ect_date = datetime.datetime.combine(datetime.datetime.now(tz=pytz.timezone('US/Eastern')), datetime.time())
        sc, lg, league_id, current_week, start_date, end_date = init_configuration(league_name=league_name, week=week)

        """ update local_db with players averages and schedule (update_db_with_players_averages function): """
        reformatted_today_date = ect_date.strftime("%Y-%m-%d")

        """ get weekly projection stats for each team/matchup (weekly_matchups_projections function): """
        weekly_matchups_projections(sc=sc, lg=lg, league_id=league_id, end_date=end_date,
                                    league_name=league_name, current_week=current_week, engine=engine)
        print("Weekly projection stats for each matchup (weekly_matchups_projections function): DONE")

        # if ect_date.weekday() == 0:
        if 1:
            """
            Distribution of played games by team (distribution_of_played_games_by_team function):
                - creates a played_games_ranking.png file with a plot of the distribution of played games by team
            """
            distribution_of_played_games_by_team(sc, lg, current_week=current_week, league_name=league_name, plot=False)
            print("Distribution of played games by team (distribution_of_played_games_by_team function): DONE")

            """
            Best FA pickup (best_FA_pickup function):
                - creates a best_FA_pickup.txt file with the best FA pickup for the week
                - creates a best_pickup_pie_{week}.png file with a pie chart of the best FA pickup for the week
            """
            best_FA_pickup(sc, lg, league_id, current_week=current_week, league_name=league_name)
            print("Best FA pickup (best_FA_pickup function): DONE")

            """
            Weekly summary by matchup (weekly_summary_by_matchup function)):
                - creates a league_cross_matchups_summary.txt file with the summary of each manager's matchup against other managers
                - creates a week_{week}_average_place.txt file with the average place of each manager for each category
                - creates a week_{week}_best_worst_category.txt file with the best and worst manager for each category
                - creates a weekly_{week}_stats_my_manager.png file with a plot of each manager's stats for the week    
            """
            weekly_summary_by_matchup(lg, week=current_week, plot=False, league_name=league_name)
            print("Weekly summary by matchup (weekly_summary_by_matchup function): DONE")
