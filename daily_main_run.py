import logging
import datetime
import pandas as pd
from yahoo_oauth import OAuth2

from custom_api.weekly_projections import weekly_matchups_projections
from custom_api.FA_analysis import get_weekly_FA_projection

from utils import init_configuration, init_db_config


if __name__ == '__main__':
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)
    logging.disable(logging.WARNING)

    week = 13

    engine = init_db_config(path_to_db_config='config.ini')
    sc = OAuth2(None, None, from_file='oauth2.json')
    totals_df = pd.read_sql_table('players_season_totals', engine)
    info_df = pd.read_sql_table('players_personal_info', engine)
    totals_df.to_sql('players_season_totals', engine, if_exists='replace', index=False)

    for league_name in ["Sheniuk", "Ootan"]:
        sc, lg, league_id, current_week, _, end_date = init_configuration(league_name=league_name, week=week,
                                                                          from_file='oauth2.json')
        output_filename = f"outputs/Excels/{league_name}/week-{current_week}_projections.xlsx"
        weekly_matchups_projections(sc=sc, lg=lg, league_id=league_id, end_date=end_date, league_name=league_name,
                                    current_week=current_week, output_filename=output_filename, engine=engine)

        start_date = datetime.datetime.today().date()
        end_date = start_date + datetime.timedelta(days=1)
        reformatted_date = f"{start_date.strftime('%b_%d')}-{end_date.strftime('%b_%d')}"
        fa_projections = get_weekly_FA_projection(sc, league_id, start_date, end_date, engine=engine)
        fa_projections.to_csv(f"outputs/Excels/{league_name}/FA_proj_{reformatted_date}.csv")