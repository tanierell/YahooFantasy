import numpy as np
import pandas as pd
import datetime
import pytz


def is_us_east_coast_time_after_7pm():
    eastern_timezone = pytz.timezone('US/Eastern')
    now_east_coast = datetime.datetime.now(eastern_timezone)

    return now_east_coast.hour >= 19


def generate_dates():
    if is_us_east_coast_time_after_7pm():
        # If it's after 7 PM in the US East Coast, start from tomorrow
        current_date = datetime.datetime.now() + datetime.timedelta(days=1)
    else:
        # If it's before 7 PM in the US East Coast, start from today
        current_date = datetime.datetime.now()

    dates = []
    if current_date.weekday() == 0:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += datetime.timedelta(days=1)

    while current_date.weekday() != 0:  # Continue until Monday (weekday value 0)
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += datetime.timedelta(days=1)

    return dates


def fetch_team_data(team_name, all_text):
    full_cols = ["Players", "Position", "Playing Status", "Opp", "Status", "Pre-Season", "Current", "FGM/A*", "FG%",
                 "FTM/A*", "FT%", "3PTM", "PTS", "REB", "AST", "ST", "BLK", "TO"]
    full_df = pd.DataFrame(columns=full_cols)

    "replacing strings to clean raw text"
    replacements = ["New Player Note", "Player Note", 'No new player Notes', '    ', "Video Forecast", "-/-", "\n", "\n"]
    for r in replacements:
        all_text = all_text.replace(r, "0/0") if r == "-/-" else all_text.replace(r, "- - -" if "Note" in r else "")

    start_date_idx = all_text.find("Players roster for ")
    dot_idx = all_text.find(".", start_date_idx)
    stats_date = all_text[start_date_idx + 19: dot_idx]
    start_index = all_text.find("- - -")
    if "Roster Edit Mode" in all_text:
        end_index = all_text.find("Roster Edit Mode")
        relevant_text = all_text[start_index:end_index].split("\n")[1:-3]
    else:
        end_index = all_text.find("Legends and Glossaries")
        relevant_text = all_text[start_index:end_index].split("\n")[1:]

    "splitting to players"
    players_lists = "\n".join(relevant_text).split("- - -")

    for player in players_lists:
        pre_data = [x for x in player.split("\n") if x != "" and "%" not in x]
        try:
            "if last index is the next player's position, remove it"
            last_num = float(pre_data[-1])
            data = pre_data
        except ValueError:
            data = pre_data[:-1]

        player_name, player_pos = data[0].split(" - ")
        if data[1] not in ["GTD", "O", "OFS", "INJ"]:
            flag = 0
            injury_type = "H"

        else:
            flag = 1
            injury_type = data[1]

        'checking if the player is playing today, else there will be just pre-season rank'
        try:
            non_game = int(data[1 + flag])
            opp = "NA"
            status = "NA"
            pre_season, current, fgm_a, fg_pct, ftm_a, ft_pct, tpm, pts, reb, ast, st, blk, to = data[1+flag:]

        except ValueError:
            opp, status, pre_season, current, fgm_a, fg_pct, ftm_a, ft_pct, tpm, pts, reb, ast, st, blk, to = data[1+flag:]

        'adding the player to the dataframe'
        full_df.loc[len(full_df)] = [player_name, player_pos, injury_type, opp, status, pre_season, current,
                                     fgm_a, fg_pct, ftm_a, ft_pct, tpm, pts, reb, ast, st, blk, to]

    df = full_df.copy()
    df["FGM"], df["FGA"] = zip(*df["FGM/A*"].apply(lambda x: x.split('/') if '/' in x else (x, x)))
    df["FTM"], df["FTA"] = zip(*df["FTM/A*"].apply(lambda x: x.split('/') if '/' in x else (x, x)))

    projected_stats_columns = ["Players", "FGM", "FGA", "FTM", "FTA", "3PTM", "PTS", "REB", "AST", "ST", "BLK", "TO"]
    df = df[projected_stats_columns]

    for col in df.columns:
        if col != "Players":
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df.rename(columns={"Players": f"{team_name} - Players"}, inplace=True)
    return df, stats_date


if __name__ == '__main__':
    dates = generate_dates()
    all_teams_text = {
        "Tani_1": ["""Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
7-11-0
9th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 563 (-4)
Best Finish: Bronze (1x)
Record: 8-14-2
Winning %: .375
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs GONzalo pipita 14-4-0 2nd
 
Week 2 Results
Loss 2 - 7
vs Dor's Penetration squad

You have used 1 of your 4 player adds for this week.

You have used 0 of 3 IL positions and 0 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Mon, Nov 6
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-06.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
Alex Caruso CHI - PG,SG
GTD
UTA
3:00 am
166
-
12%
2.3/5.2
.449
1.1/1.4
.798
1
6.8
3.2
2.9
1.4
0.7
1.2
SG
Player Note
De'Anthony Melton PHI - PG,SG
WAS
2:00 am
106
-
40%
3.2/7.5
.431
0.9/1.1
.801
1.7
9.1
3.9
3.3
1.2
0.4
1.4
G
Player Note
Damian Lillard MIL - PG
@BKN
2:30 am
10
-
86%
7.5/16.3
.460
5.8/6.6
.889
3
23.9
4.7
6.4
0.9
0.3
2.9
SF
Player Note
Jalen Williams OKC - SG,SF,PF
ATL
3:00 am
60
-
76%
6.8/12.8
.528
2.9/3.5
.846
1.2
17.6
5.7
3.6
1.5
0.4
1.8
PF
New Player Note
Patrick Williams CHI - PF
GTD
UTA
3:00 am
157
-
15%
3.1/6.7
.457
1.0/1.2
.818
1.1
8.2
3.3
1.1
0.7
0.6
1
F
No new player Notes
Kyle Anderson MIN - SF,PF
BOS
3:00 am
159
-
24%
3.2/6.7
.483
1.2/1.6
.749
0.7
8.3
4.6
3.3
1
0.6
1.2
C
Player Note
Walker Kessler UTA - C
Video Forecast
@CHI
3:00 am
54
-
80%
4.2/6.1
.681
1.2/2.1
.537
0.1
9.6
10.3
1.3
0.5
2
1
C
Player Note
Anthony Davis LAL - PF,C
@MIA
2:30 am
9
-
94%
7.7/14.2
.545
4.4/5.7
.765
0.4
20.2
13.2
2.5
1
1.5
2
Util
Player Note
Brook Lopez MIL - C
@BKN
2:30 am
76
-
73%
5.0/9.4
.533
1.5/2.0
.749
1.2
12.8
7.3
1.2
0.5
2.1
1.3
Util
Player Note
Josh Hart NYK - SG,SF
LAC
2:30 am
147
-
25%
3.2/6.3
.508
1.3/1.8
.765
0.8
8.6
6.5
2.8
0.9
0.2
1.3
BN
New Player Note
OG Anunoby TOR - SG,SF
49
-
51%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Grayson Allen PHX - SG,SF
170
-
9%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Brandon Miller CHA - SF
132
-
25%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
7-11-0
  |  
9th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
There are no sit/start suggestions available right now. Check back later!
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
7-11-0
9th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 563 (-4)
Best Finish: Bronze (1x)
Record: 8-14-2
Winning %: .375
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs GONzalo pipita 14-4-0 2nd
 
Week 2 Results
Loss 2 - 7
vs Dor's Penetration squad

You have used 1 of your 4 player adds for this week.

You have used 0 of 3 IL positions and 0 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Wed, Nov 8
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-08.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
Alex Caruso CHI - PG,SG
GTD
PHX
3:00 am
166
-
2.3/5.1
.445
1.2/1.5
.796
0.9
6.6
3.2
2.8
1.4
0.7
1.3
SG
Player Note
De'Anthony Melton PHI - PG,SG
BOS
2:00 am
106
-
3.2/7.4
.424
0.8/1.1
.790
1.6
8.8
3.9
3.1
1.2
0.4
1.4
G
Player Note
Damian Lillard MIL - PG
DET
3:00 am
10
-
7.5/16.0
.469
5.9/6.6
.890
3
24
4.7
6.6
0.9
0.3
2.9
SF
Player Note
Jalen Williams OKC - SG,SF,PF
CLE
3:00 am
60
-
5.4/10.7
.507
1.9/2.4
.788
1.2
14
5.5
3.1
1.3
0.4
1.6
PF
New Player Note
Patrick Williams CHI - PF
GTD
PHX
3:00 am
157
-
3.0/6.5
.452
1.0/1.2
.827
1
8
3.4
1.1
0.7
0.6
1
F
No new player Notes
Kyle Anderson MIN - SF,PF
NOP
3:00 am
159
-
3.2/6.6
.488
1.3/1.7
.755
0.7
8.4
4.7
3.5
1
0.7
1.2
C
Player Note
Walker Kessler UTA - C
Video Forecast
@IND
2:00 am
54
-
4.5/6.5
.686
1.3/2.4
.559
0.1
10.4
11.1
1.4
0.5
2.1
1
C
Player Note
Anthony Davis LAL - PF,C
@HOU
3:00 am
9
-
8.4/15.5
.543
5.2/6.8
.769
0.4
22.5
14.5
2.9
1.2
1.8
2.2
Util
Player Note
Brook Lopez MIL - C
DET
3:00 am
76
-
5.0/9.1
.550
1.5/2.0
.752
1.2
12.7
7.2
1.3
0.5
2.3
1.3
Util
Player Note
Josh Hart NYK - SG,SF
SAS
2:30 am
147
-
3.1/5.9
.530
1.3/1.7
.763
0.7
8.3
6.1
2.7
0.9
0.2
1.2
BN
New Player Note
OG Anunoby TOR - SG,SF
@DAL
3:30 am
49
-
5.5/11.7
.474
1.9/2.3
.837
2
15
5.1
1.9
1.7
0.7
1.6
BN
New Player Note
Grayson Allen PHX - SG,SF
@CHI
3:00 am
170
-
3.1/7.3
.423
1.0/1.2
.863
1.9
9.1
3.5
2.2
0.8
0.2
0.9
BN
New Player Note
Brandon Miller CHA - SF
WAS
2:00 am
132
-
5.4/12.2
.447
3.3/4.1
.823
1.8
16.1
7.4
1.9
1
0.8
2
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
7-11-0
  |  
9th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Photo of OG AnunobyPhoto of De'Anthony Melton
OG Anunoby
De'Anthony Melton
Compare
Photo of Brandon MillerPhoto of Josh Hart
Brandon Miller
Josh Hart
Compare
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
7-11-0
9th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 563 (-4)
Best Finish: Bronze (1x)
Record: 8-14-2
Winning %: .375
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs GONzalo pipita 14-4-0 2nd
 
Week 2 Results
Loss 2 - 7
vs Dor's Penetration squad

You have used 1 of your 4 player adds for this week.

You have used 0 of 3 IL positions and 0 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Thu, Nov 9
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-09.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
Alex Caruso CHI - PG,SG
GTD
166
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
De'Anthony Melton PHI - PG,SG
106
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
G
Player Note
Damian Lillard MIL - PG
@IND
2:00 am
10
-
8.4/17.8
.474
8.2/9.0
.919
3.6
28.7
5.2
7.1
1
0.4
3.2
SF
Player Note
Jalen Williams OKC - SG,SF,PF
60
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
New Player Note
Patrick Williams CHI - PF
GTD
157
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
No new player Notes
Kyle Anderson MIN - SF,PF
159
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Walker Kessler UTA - C
Video Forecast
54
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Anthony Davis LAL - PF,C
9
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Brook Lopez MIL - C
@IND
2:00 am
76
-
4.8/10.1
.479
2.0/2.3
.872
1.7
13.3
5.4
0.7
0.9
2.3
1.3
Util
Player Note
Josh Hart NYK - SG,SF
147
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
OG Anunoby TOR - SG,SF
49
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Grayson Allen PHX - SG,SF
170
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Brandon Miller CHA - SF
132
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
7-11-0
  |  
9th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
There are no sit/start suggestions available right now. Check back later!
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
7-11-0
9th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 563 (-4)
Best Finish: Bronze (1x)
Record: 8-14-2
Winning %: .375
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs GONzalo pipita 14-4-0 2nd
 
Week 2 Results
Loss 2 - 7
vs Dor's Penetration squad

You have used 1 of your 4 player adds for this week.

You have used 0 of 3 IL positions and 0 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Fri, Nov 10
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-10.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
Alex Caruso CHI - PG,SG
GTD
166
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
De'Anthony Melton PHI - PG,SG
@DET
2:00 am
106
-
3.0/7.7
.388
0.9/1.2
.720
1.6
8.4
3.8
3.9
1.4
0.6
1.5
G
Player Note
Damian Lillard MIL - PG
10
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Jalen Williams OKC - SG,SF,PF
@SAC
5:00 am
60
-
6.8/13.4
.503
2.8/3.4
.821
1.3
17.6
5.1
4.5
1.3
0.3
2.2
PF
New Player Note
Patrick Williams CHI - PF
GTD
157
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
No new player Notes
Kyle Anderson MIN - SF,PF
@SAS
3:00 am
159
-
3.7/7.0
.537
1.3/1.7
.767
0.4
9.2
4.4
4
1.2
1
1.2
C
Player Note
Walker Kessler UTA - C
Video Forecast
@MEM
3:00 am
54
-
4.6/7.2
.634
1.1/2.1
.533
0
10.3
9.6
0.9
0.4
2.9
1
C
Player Note
Anthony Davis LAL - PF,C
@PHX
5:00 am
9
-
9.7/18.1
.536
5.9/7.3
.808
0.4
25.7
12.9
2.6
1.3
2.3
2.1
Util
Player Note
Brook Lopez MIL - C
76
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Josh Hart NYK - SG,SF
147
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
OG Anunoby TOR - SG,SF
49
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Grayson Allen PHX - SG,SF
LAL
5:00 am
170
-
2.1/4.7
.442
0.5/0.6
.916
1.2
5.9
2
1.2
0.3
0.1
0.6
BN
New Player Note
Brandon Miller CHA - SF
@WAS
2:00 am
132
-
5.6/12.8
.438
3.2/3.9
.835
1.8
16.2
6.6
1.8
0.7
0.9
1.6
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
7-11-0
  |  
9th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Photo of Brandon MillerPhoto of Josh Hart
Brandon Miller
Josh Hart
Compare
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
7-11-0
9th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 563 (-4)
Best Finish: Bronze (1x)
Record: 8-14-2
Winning %: .375
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs GONzalo pipita 14-4-0 2nd
 
Week 2 Results
Loss 2 - 7
vs Dor's Penetration squad

You have used 1 of your 4 player adds for this week.

You have used 0 of 3 IL positions and 0 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Sat, Nov 11
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-11.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
Alex Caruso CHI - PG,SG
GTD
166
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
De'Anthony Melton PHI - PG,SG
106
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
G
Player Note
Damian Lillard MIL - PG
@ORL
1:00 am
10
-
7.8/17.0
.458
7.1/7.7
.919
3.6
26.2
4.7
6.7
0.9
0.3
3
SF
Player Note
Jalen Williams OKC - SG,SF,PF
60
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
New Player Note
Patrick Williams CHI - PF
GTD
157
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
No new player Notes
Kyle Anderson MIN - SF,PF
159
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Walker Kessler UTA - C
Video Forecast
54
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Anthony Davis LAL - PF,C
9
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Brook Lopez MIL - C
@ORL
1:00 am
76
-
4.3/9.1
.465
1.6/1.9
.872
1.6
11.7
4.4
0.6
0.8
2
1.1
Util
Player Note
Josh Hart NYK - SG,SF
147
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
OG Anunoby TOR - SG,SF
@BOS
2:00 am
49
-
6.0/12.6
.476
1.3/1.8
.744
2.2
15.6
4.8
2
1.4
0.5
1.4
BN
New Player Note
Grayson Allen PHX - SG,SF
170
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Brandon Miller CHA - SF
132
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
7-11-0
  |  
9th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Photo of OG AnunobyPhoto of De'Anthony Melton
OG Anunoby
De'Anthony Melton
Compare
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
7-11-0
9th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 563 (-4)
Best Finish: Bronze (1x)
Record: 8-14-2
Winning %: .375
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs GONzalo pipita 14-4-0 2nd
 
Week 2 Results
Loss 2 - 7
vs Dor's Penetration squad

You have used 1 of your 4 player adds for this week.

You have used 0 of 3 IL positions and 0 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Sun, Nov 12
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-12.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
Alex Caruso CHI - PG,SG
GTD
DET
2:00 am
166
-
2.6/5.5
.468
1.2/1.7
.733
1
7.4
3.9
2.9
1.7
0.7
1.1
SG
Player Note
De'Anthony Melton PHI - PG,SG
IND
1:00 am
106
-
3.1/7.9
.390
0.9/1.2
.720
1.7
8.7
3.9
4.1
1.5
0.6
1.7
G
Player Note
Damian Lillard MIL - PG
10
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Jalen Williams OKC - SG,SF,PF
@PHX
3:00 am
60
-
6.1/12.7
.477
3.0/3.6
.821
1.2
16.4
5
3.8
1.2
0.3
2.2
PF
New Player Note
Patrick Williams CHI - PF
GTD
DET
2:00 am
157
-
2.6/5.7
.452
1.7/2.1
.811
0.6
7.5
3.7
1
0.9
0.6
0.9
F
No new player Notes
Kyle Anderson MIN - SF,PF
@GSW
3:30 am
159
-
3.4/6.8
.497
1.4/1.8
.766
0.5
8.5
4.3
3.8
1.2
0.8
1.2
C
Player Note
Walker Kessler UTA - C
Video Forecast
54
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Anthony Davis LAL - PF,C
POR
5:00 am
9
-
9.6/16.9
.565
5.2/6.4
.808
0.4
24.7
12.1
2.8
1.3
2.3
1.8
Util
Player Note
Brook Lopez MIL - C
76
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Josh Hart NYK - SG,SF
CHA
7:00 pm
147
-
2.7/5.8
.471
1.2/1.5
.764
0.7
7.3
6.6
2.6
0.8
0.4
1.2
BN
New Player Note
OG Anunoby TOR - SG,SF
49
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Grayson Allen PHX - SG,SF
OKC
3:00 am
170
-
2.1/4.5
.458
0.7/0.7
.916
1.3
6.1
2.1
1.2
0.3
0.1
0.7
BN
New Player Note
Brandon Miller CHA - SF
@NYK
7:00 pm
132
-
5.2/12.2
.428
3.4/4.0
.835
1.9
15.7
6.2
1.8
0.6
0.8
1.7
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
7-11-0
  |  
9th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Photo of Brandon MillerPhoto of Josh Hart
Brandon Miller
Josh Hart
Compare
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved."""], "Gon": ["""Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoGold level
 
GONzalo pipita 
Gon SINCE '19 View Profile
14-4-0
2nd Place
 
Level: gold LEVEL: GOLD 
Rating: 772 (-5)
Best Finish: Gold (3x)
Record: 81-52-3
Winning %: .607
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 7-11-0 9th
 
Week 2 Results
Won 6 - 3
vs Yali's Carnaval
 
Mon, Nov 6
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
GONzalo pipita's Players roster for 2023-11-06.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Tre Jones SAS - PG


@IND
2:00 am
103
-
63%
4.6/9.8
.465
2.2/2.5
.878
0.8
12.1
4
6.4
1.3
0.1
1.6
SG
Player Note
Anthony Edwards MIN - SG,SF


BOS
3:00 am
15
-
92%
8.1/18.3
.441
3.3/4.3
.767
2.6
22
5.5
3.5
1.5
0.6
2.7
G
New Player Note
Stephen Curry GSW - PG


@DET
2:00 am
7
-
99%
8.5/17.6
.481
4.7/5.2
.906
3.8
25.4
5.9
5.2
0.8
0.4
3.1
SF
Player Note
Tobias Harris PHI - SF,PF


WAS
2:00 am
65
-
79%
5.7/11.5
.494
1.5/1.8
.859
1.7
14.6
6.6
3.3
0.8
0.5
1.4
PF
Player Note
Dorian Finney-Smith BKN - SF,PF


Video Forecast
MIL
2:30 am
194
-
30%
4.2/10.0
.414
1.0/1.3
.754
2.1
11.4
7.3
1.7
1
0.9
1.2
F
Player Note
Kentavious Caldwell-Pope DEN - SG,SF


NOP
4:00 am
118
-
46%
4.4/10.0
.443
1.6/2.0
.835
2.1
12.6
3.4
2.8
1.5
0.5
1.5
C
New Player Note
Xavier Tillman Sr. MEM - PF,C
GTD


127
-
16%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Alperen Sengun HOU - C


SAC
3:00 am
58
-
88%
6.0/10.2
.589
2.6/3.6
.705
0.3
14.9
10.8
3.6
0.9
1
2.8
Util
Player Note
Kawhi Leonard LAC - SG,SF


@NYK
2:30 am
20
-
81%
7.5/14.9
.501
3.4/4.0
.856
2
20.3
6.7
2.8
1.2
0.6
1.4
Util
Player Note
Spencer Dinwiddie BKN - PG,SG


MIL
2:30 am
109
-
60%
5.8/12.7
.456
2.8/3.5
.804
2.1
16.5
4
5
0.8
0.3
1.7
BN
Player Note
Jeremy Sochan SAS - PG,PF


@IND
2:00 am
131
-
43%
4.2/8.8
.469
1.5/2.1
.722
0.7
10.5
6.1
2.5
0.8
0.3
1.7
BN
Player Note
Pascal Siakam TOR - PF,C


Video Forecast
33
-
55%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Deandre Ayton POR - C


63
-
58%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
No new player Notes
Trey Murphy III NOP - SF,PF
INJ


@DEN
4:00 am
149
-
10%
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL
Player Note
Cameron Johnson BKN - SF,PF
INJ


MIL
2:30 am
68
-
24%
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL+
New Player Note
Markelle Fultz ORL - PG,SG
GTD


DAL
2:00 am
94
-
43%
5.5/10.5
.523
1.8/2.2
.799
0.6
13.4
4.3
4.7
1
0.4
2.1
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoGold level
 
GONzalo pipita 
Gon SINCE '19 View Profile
14-4-0
2nd Place
 
Level: gold LEVEL: GOLD 
Rating: 772 (-5)
Best Finish: Gold (3x)
Record: 81-52-3
Winning %: .607
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 7-11-0 9th
 
Week 2 Results
Won 6 - 3
vs Yali's Carnaval
 
Wed, Nov 8
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
GONzalo pipita's Players roster for 2023-11-08.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
Stephen Curry GSW - PG


@DEN
5:00 am
7
-
8.5/17.8
.476
4.5/5.0
.909
3.7
25.2
5.8
5.3
0.8
0.3
3.1
SG
Player Note
Kentavious Caldwell-Pope DEN - SG,SF


GSW
5:00 am
118
-
4.2/9.5
.444
1.7/2.0
.838
1.9
12.1
3.6
2.6
1.6
0.5
1.4
G
Player Note
Tre Jones SAS - PG


@NYK
2:30 am
103
-
4.1/8.9
.456
1.8/2.1
.866
0.7
10.7
3.5
5.8
1.2
0.1
1.4
SF
Player Note
Tobias Harris PHI - SF,PF


BOS
2:00 am
65
-
5.5/11.3
.491
1.5/1.7
.849
1.7
14.2
6.6
3.1
0.8
0.5
1.4
PF
Player Note
Dorian Finney-Smith BKN - SF,PF


Video Forecast
LAC
2:30 am
194
-
3.6/8.7
.416
0.9/1.2
.786
1.9
10.1
5.8
1.5
0.8
0.5
1.1
F
Player Note
Anthony Edwards MIN - SG,SF


NOP
3:00 am
15
-
8.1/18.3
.443
3.5/4.6
.769
2.7
22.5
5.5
3.6
1.5
0.6
2.9
C
Player Note
Alperen Sengun HOU - C


LAL
3:00 am
58
-
5.7/9.8
.583
2.4/3.4
.700
0.3
14.1
10.2
3.6
0.9
1
2.6
C
Player Note
Pascal Siakam TOR - PF,C


Video Forecast
@DAL
3:30 am
33
-
7.4/15.2
.484
4.2/5.4
.782
1.3
20.2
7.9
4.8
0.9
0.5
1.9
Util
Player Note
Kawhi Leonard LAC - SG,SF


@BKN
2:30 am
20
-
7.4/14.8
.499
3.3/3.9
.840
1.9
20
6.8
2.6
1.2
0.6
1.4
Util
Player Note
Spencer Dinwiddie BKN - PG,SG


LAC
2:30 am
109
-
5.5/12.4
.445
2.9/3.5
.824
2.3
16.2
3.6
5.2
0.8
0.3
1.7
BN
Player Note
Jeremy Sochan SAS - PG,PF


@NYK
2:30 am
131
-
4.3/9.5
.454
1.5/2.1
.723
0.8
10.9
6.2
2.7
0.8
0.3
1.7
BN
New Player Note
Xavier Tillman Sr. MEM - PF,C
GTD


MIA
3:00 am
127
-
3.9/6.6
.591
1.2/2.1
.580
0.2
9.2
6.6
2.1
1
0.4
0.9
BN
Player Note
Deandre Ayton POR - C


@SAC
5:00 am
63
-
6.8/11.5
.590
2.6/3.4
.765
0.2
16.4
10.4
2.1
0.5
0.7
1.9
IL
No new player Notes
Trey Murphy III NOP - SF,PF
INJ


@MIN
3:00 am
149
-
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL
Player Note
Cameron Johnson BKN - SF,PF
INJ


LAC
2:30 am
68
-
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL+
New Player Note
Markelle Fultz ORL - PG,SG
GTD


94
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoGold level
 
GONzalo pipita 
Gon SINCE '19 View Profile
14-4-0
2nd Place
 
Level: gold LEVEL: GOLD 
Rating: 772 (-5)
Best Finish: Gold (3x)
Record: 81-52-3
Winning %: .607
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 7-11-0 9th
 
Week 2 Results
Won 6 - 3
vs Yali's Carnaval
 
Fri, Nov 10
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
GONzalo pipita's Players roster for 2023-11-10.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Tre Jones SAS - PG


MIN
3:00 am
103
-
4.2/9.2
.455
2.2/2.5
.882
0.4
11
3.3
5.6
1.1
0.2
1.3
SG
Player Note
Anthony Edwards MIN - SG,SF


@SAS
3:00 am
15
-
10.3/20.7
.497
4.0/5.2
.783
3
27.5
5.9
4.8
1.6
0.5
2.9
G
New Player Note
Stephen Curry GSW - PG


7
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Tobias Harris PHI - SF,PF


@DET
2:00 am
65
-
6.8/12.5
.546
2.9/3.5
.833
1.7
18.2
6.7
3.1
0.9
0.7
1.7
PF
Player Note
Dorian Finney-Smith BKN - SF,PF


Video Forecast
@BOS
2:30 am
194
-
3.6/7.8
.464
0.3/0.5
.583
2
9.6
4.4
1.2
0.5
0.3
0.8
F
Player Note
Jeremy Sochan SAS - PG,PF


MIN
3:00 am
131
-
4.5/10.3
.434
1.9/2.6
.735
0.6
11.4
5.5
3.8
1.2
0.4
2.1
C
New Player Note
Xavier Tillman Sr. MEM - PF,C
GTD


UTA
3:00 am
127
-
2.8/5.9
.480
0.8/1.4
.567
0.2
6.7
4.7
1.5
1.2
0.5
0.8
C
Player Note
Alperen Sengun HOU - C


NOP
3:00 am
58
-
6.0/10.5
.566
2.6/3.8
.691
0.5
15
8
4.2
0.9
0.8
2.7
Util
Player Note
Kawhi Leonard LAC - SG,SF


@DAL
3:30 am
20
-
8.6/17.6
.491
4.6/5.5
.835
2.3
24.2
6.7
4
1.3
0.3
1.8
Util
Player Note
Spencer Dinwiddie BKN - PG,SG


@BOS
2:30 am
109
-
4.6/11.0
.420
2.1/2.8
.746
1.6
13
3.2
5
0.5
0.1
1.3
BN
Player Note
Kentavious Caldwell-Pope DEN - SG,SF


118
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Pascal Siakam TOR - PF,C


Video Forecast
33
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Deandre Ayton POR - C


63
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
No new player Notes
Trey Murphy III NOP - SF,PF
INJ


@HOU
3:00 am
149
-
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL
Player Note
Cameron Johnson BKN - SF,PF
INJ


@BOS
2:30 am
68
-
4.8/10.3
.466
1.8/2.1
.841
2.1
13.5
4
1.3
1
0.2
0.6
IL+
New Player Note
Markelle Fultz ORL - PG,SG
GTD


94
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoGold level
 
GONzalo pipita 
Gon SINCE '19 View Profile
14-4-0
2nd Place
 
Level: gold LEVEL: GOLD 
Rating: 772 (-5)
Best Finish: Gold (3x)
Record: 81-52-3
Winning %: .607
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 7-11-0 9th
 
Week 2 Results
Won 6 - 3
vs Yali's Carnaval
 
Sat, Nov 11
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
GONzalo pipita's Players roster for 2023-11-11.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Tre Jones SAS - PG


103
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
Anthony Edwards MIN - SG,SF


15
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
G
New Player Note
Stephen Curry GSW - PG


CLE
3:30 am
7
-
8.0/16.2
.495
4.1/4.5
.923
4.2
24.4
4.8
4.4
1
0.2
3.4
SF
Player Note
Tobias Harris PHI - SF,PF


65
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
Player Note
Pascal Siakam TOR - PF,C


Video Forecast
@BOS
2:00 am
33
-
6.8/14.9
.455
2.8/3.6
.765
1.1
17.4
6.8
4.1
0.8
0.3
1.9
F
Player Note
Jeremy Sochan SAS - PG,PF


131
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
New Player Note
Xavier Tillman Sr. MEM - PF,C
GTD


127
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Alperen Sengun HOU - C


58
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Kawhi Leonard LAC - SG,SF


20
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Spencer Dinwiddie BKN - PG,SG


109
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Dorian Finney-Smith BKN - SF,PF


Video Forecast
194
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Kentavious Caldwell-Pope DEN - SG,SF


118
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Deandre Ayton POR - C


63
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
No new player Notes
Trey Murphy III NOP - SF,PF
INJ


149
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Cameron Johnson BKN - SF,PF
INJ


68
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
New Player Note
Markelle Fultz ORL - PG,SG
GTD


MIL
1:00 am
94
-
6.1/12.8
.474
1.3/1.7
.764
0.4
13.8
3.8
5.3
1.4
0.3
1.8
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat

logoGold level
 
GONzalo pipita 
Gon SINCE '19 View Profile
14-4-0
2nd Place
 
Level: gold LEVEL: GOLD 
Rating: 772 (-5)
Best Finish: Gold (3x)
Record: 81-52-3
Winning %: .607
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 7-11-0 9th
 
Week 2 Results
Won 6 - 3
vs Yali's Carnaval
 
Sun, Nov 12
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
GONzalo pipita's Players roster for 2023-11-12.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Tre Jones SAS - PG


MIA
2:00 am
103
-
3.8/7.9
.475
1.7/2.0
.882
0.5
9.7
3
5.5
0.9
0.1
1.2
SG
Player Note
Anthony Edwards MIN - SG,SF


@GSW
3:30 am
15
-
9.5/20.6
.459
4.3/5.5
.783
3
26.3
5.8
4.5
1.5
0.4
3
G
New Player Note
Stephen Curry GSW - PG


MIN
3:30 am
7
-
9.2/18.3
.501
5.0/5.4
.922
4.9
28.2
5.5
5
1.2
0.2
3.5
SF
Player Note
Tobias Harris PHI - SF,PF


IND
1:00 am
65
-
7.0/13.0
.539
2.9/3.5
.833
1.8
18.7
6.8
3.3
0.9
0.7
1.9
PF
Player Note
Dorian Finney-Smith BKN - SF,PF


Video Forecast
WAS
10:00 pm
194
-
3.7/7.7
.480
0.3/0.5
.584
2.1
9.8
4.4
1.4
0.5
0.4
0.8
F
Player Note
Jeremy Sochan SAS - PG,PF


MIA
2:00 am
131
-
4.1/9.0
.452
1.5/2.0
.735
0.6
10.2
4.9
3.7
1
0.3
2.1
C
New Player Note
Xavier Tillman Sr. MEM - PF,C
GTD


@LAC
10:30 pm
127
-
2.7/5.6
.482
0.7/1.3
.567
0.2
6.3
4.4
1.5
1.1
0.4
0.8
C
Player Note
Alperen Sengun HOU - C


DEN
2:00 am
58
-
6.2/11.0
.562
2.5/3.6
.691
0.4
15.2
7.8
4.2
1
0.7
2.4
Util
Player Note
Kawhi Leonard LAC - SG,SF


MEM
10:30 pm
20
-
8.9/19.2
.464
4.6/5.5
.835
2.8
25.1
6.9
4.5
1.4
0.5
2.1
Util
Player Note
Spencer Dinwiddie BKN - PG,SG


WAS
10:00 pm
109
-
4.7/11.0
.430
2.2/3.0
.746
1.7
13.4
3.1
5.5
0.5
0.1
1.3
BN
Player Note
Pascal Siakam TOR - PF,C


Video Forecast
33
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Kentavious Caldwell-Pope DEN - SG,SF


@HOU
2:00 am
118
-
4.4/9.8
.451
1.6/1.8
.869
2.5
13
2.7
2
2
0.6
1.3
BN
Player Note
Deandre Ayton POR - C


@LAL
5:00 am
63
-
7.4/13.0
.571
1.5/1.9
.760
0
16.3
11.5
1.6
1.2
0.9
1.6
IL
No new player Notes
Trey Murphy III NOP - SF,PF
INJ


DAL
2:00 am
149
-
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL
Player Note
Cameron Johnson BKN - SF,PF
INJ


WAS
10:00 pm
68
-
4.9/10.2
.479
1.9/2.3
.841
2.1
13.9
3.9
1.5
1.1
0.2
0.6
IL+
New Player Note
Markelle Fultz ORL - PG,SG
GTD


94
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved."""],
        "Ootan": ["""Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoBronze level
 
Big O’s team 
Yonatan SINCE '23 View Profile
6-12-0
10th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 586 (-4)
Best Finish: N/A
Record: 0-2-0
Winning %: .000
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Tal's Top-Notch Team 4-14-0 11th
 
Week 2 Results
Loss 2 - 7
vs Earth is flat 🍟
 
Mon, Nov 6
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Big O’s team's Players roster for 2023-11-06.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
LaMelo Ball CHA - PG,SG


11
-
59%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
Austin Reaves LAL - SG,SF


@MIA
2:30 am
107
-
71%
4.2/8.5
.493
2.8/3.4
.841
1.7
12.9
3.7
3.6
0.7
0.3
1.6
G
Player Note
Bogdan Bogdanovic ATL - SG,SF,PF


@OKC
3:00 am
177
-
33%
4.2/9.3
.447
1.0/1.2
.803
2.3
11.6
2.8
2.3
0.6
0.3
1.1
SF
Player Note
Buddy Hield IND - SG,SF


SAS
2:00 am
96
-
70%
4.8/10.2
.471
1.2/1.5
.792
2.5
13.3
4.7
2.3
1
0.3
1.5
PF
Player Note
Keegan Murray SAC - SF,PF


Video Forecast
@HOU
3:00 am
86
-
68%
5.2/11.1
.463
1.2/1.5
.753
2.7
14.2
6.1
1.6
1
0.7
1
F
Player Note
Kelly Oubre Jr. PHI - SF


WAS
2:00 am
133
-
62%
6.6/15.2
.434
2.8/3.6
.763
2.1
18
5.7
1.6
1.1
0.3
1.5
C
Player Note
Kevon Looney GSW - PF,C


@DET
2:00 am
141
-
58%
3.4/5.3
.638
1.6/2.6
.633
0
8.5
10.4
2.2
0.6
0.7
0.8
C
Player Note
Onyeka Okongwu ATL - C


@OKC
3:00 am
115
-
62%
3.5/5.5
.638
1.7/2.3
.753
0.1
8.8
7.5
1.1
0.6
1.3
1.1
Util
New Player Note
Mikal Bridges BKN - SG,SF


MIL
2:30 am
19
-
92%
8.2/16.6
.490
3.8/4.3
.878
2.2
22.3
6
3
1.1
0.9
1.7
Util
New Player Note
Daniel Gafford WAS - PF,C
GTD


@PHI
2:00 am
108
-
40%
4.9/6.8
.726
2.1/3.0
.688
0.1
12
8.4
1.3
0.5
1.8
1.2
BN
New Player Note
Scottie Barnes TOR - SF,PF


45
-
53%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Drew Eubanks PHX - C


180
-
5%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Darius Garland CLE - PG


36
-
45%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
New Player Note
Nic Claxton BKN - C
INJ


MIL
2:30 am
52
-
27%
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoBronze level
 
Big O’s team 
Yonatan SINCE '23 View Profile
6-12-0
10th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 586 (-4)
Best Finish: N/A
Record: 0-2-0
Winning %: .000
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Tal's Top-Notch Team 4-14-0 11th
 
Week 2 Results
Loss 2 - 7
vs Earth is flat 🍟
 
Wed, Nov 8
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Big O’s team's Players roster for 2023-11-08.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
LaMelo Ball CHA - PG,SG


WAS
2:00 am
11
-
7.1/17.1
.417
2.4/3.0
.816
3.2
19.9
6
7.4
1.3
0.3
2.9
SG
Player Note
Austin Reaves LAL - SG,SF


@HOU
3:00 am
107
-
4.2/8.5
.495
3.0/3.5
.849
1.7
13.2
3.6
3.6
0.7
0.3
1.5
G
New Player Note
Darius Garland CLE - PG


@OKC
3:00 am
36
-
6.7/14.6
.457
3.8/4.4
.846
2
19.1
3.5
7.3
1.2
0.2
3
SF
Player Note
Buddy Hield IND - SG,SF


UTA
2:00 am
96
-
4.6/10.1
.453
1.3/1.6
.805
2.5
12.9
4.7
2.2
0.9
0.3
1.5
PF
Player Note
Keegan Murray SAC - SF,PF


Video Forecast
POR
5:00 am
86
-
4.7/10.1
.462
1.0/1.3
.765
2.5
12.8
5.7
1.5
0.8
0.5
0.9
F
Player Note
Kelly Oubre Jr. PHI - SF


BOS
2:00 am
133
-
6.4/14.9
.431
2.6/3.5
.752
2
17.5
5.7
1.5
1.1
0.3
1.5
C
Player Note
Kevon Looney GSW - PF,C


@DEN
5:00 am
141
-
3.4/5.5
.618
1.5/2.4
.635
0.1
8.4
10.2
2.3
0.6
0.7
0.8
C
New Player Note
Daniel Gafford WAS - PF,C
GTD


@CHA
2:00 am
108
-
5.3/7.3
.716
2.2/3.1
.691
0.1
12.8
8.9
1.4
0.5
1.9
1.3
Util
New Player Note
Mikal Bridges BKN - SG,SF


LAC
2:30 am
19
-
7.3/15.4
.477
3.5/3.9
.900
2.3
20.4
5.2
2.9
1
0.7
1.6
Util
New Player Note
Scottie Barnes TOR - SF,PF


@DAL
3:30 am
45
-
5.6/12.1
.464
2.3/3.0
.780
1
14.5
7.3
4.3
1.1
0.8
1.7
BN
Player Note
Onyeka Okongwu ATL - C


115
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Bogdan Bogdanovic ATL - SG,SF,PF


177
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Drew Eubanks PHX - C


@CHI
3:00 am
180
-
2.5/4.2
.590
0.8/1.3
.644
0.1
5.9
6.6
1.4
0.5
1.1
0.8
IL+
New Player Note
Nic Claxton BKN - C
INJ


LAC
2:30 am
52
-
5.4/7.6
.702
1.7/3.0
.578
0.1
12.6
10.1
1.7
0.8
2.1
1.3
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoBronze level
 
Big O’s team 
Yonatan SINCE '23 View Profile
6-12-0
10th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 586 (-4)
Best Finish: N/A
Record: 0-2-0
Winning %: .000
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Tal's Top-Notch Team 4-14-0 11th
 
Week 2 Results
Loss 2 - 7
vs Earth is flat 🍟
 
Thu, Nov 9
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Big O’s team's Players roster for 2023-11-09.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
LaMelo Ball CHA - PG,SG


11
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
Austin Reaves LAL - SG,SF


107
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
G
New Player Note
Darius Garland CLE - PG


36
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Buddy Hield IND - SG,SF


MIL
2:00 am
96
-
4.8/11.3
.429
0.6/0.7
.810
3
13.3
4
2.5
0.6
0.3
1.3
PF
Player Note
Keegan Murray SAC - SF,PF


Video Forecast
86
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
Player Note
Kelly Oubre Jr. PHI - SF


133
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Kevon Looney GSW - PF,C


141
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
New Player Note
Daniel Gafford WAS - PF,C
GTD


108
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
Mikal Bridges BKN - SG,SF


19
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
Scottie Barnes TOR - SF,PF


45
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Onyeka Okongwu ATL - C


@ORL
4:30 am
115
-
3.7/5.7
.649
2.2/2.6
.844
0.2
9.8
6.2
1.3
0.7
1.2
0.9
BN
Player Note
Bogdan Bogdanovic ATL - SG,SF,PF


@ORL
4:30 am
177
-
4.0/9.4
.421
0.7/0.8
.889
2.2
10.8
2.8
2.7
1.1
0.3
0.9
BN
Player Note
Drew Eubanks PHX - C


180
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
New Player Note
Nic Claxton BKN - C
INJ


52
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoBronze level
 
Big O’s team 
Yonatan SINCE '23 View Profile
6-12-0
10th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 586 (-4)
Best Finish: N/A
Record: 0-2-0
Winning %: .000
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Tal's Top-Notch Team 4-14-0 11th
 
Week 2 Results
Loss 2 - 7
vs Earth is flat 🍟
 
Fri, Nov 10
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Big O’s team's Players roster for 2023-11-10.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
LaMelo Ball CHA - PG,SG


@WAS
2:00 am
11
-
7.2/18.0
.401
2.9/3.4
.849
3.1
20.5
6.1
8.8
1.4
0.4
3
SG
Player Note
Austin Reaves LAL - SG,SF


@PHX
5:00 am
107
-
4.8/11.1
.429
4.3/4.9
.875
1.5
15.3
3.6
3.6
0.8
0.3
2.1
G
New Player Note
Darius Garland CLE - PG


36
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Buddy Hield IND - SG,SF


96
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
Player Note
Keegan Murray SAC - SF,PF


Video Forecast
OKC
5:00 am
86
-
5.0/11.6
.428
2.0/2.6
.784
2.7
14.7
5.6
1.7
1
0.7
1.1
F
Player Note
Kelly Oubre Jr. PHI - SF


@DET
2:00 am
133
-
6.4/13.5
.477
2.8/3.8
.727
2.8
18.4
4.7
1.1
1.4
0.5
1
C
Player Note
Kevon Looney GSW - PF,C


141
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
New Player Note
Daniel Gafford WAS - PF,C
GTD


CHA
2:00 am
108
-
4.6/6.4
.709
2.0/3.1
.667
0
11.2
7.6
1.1
0.4
2.1
1.1
Util
New Player Note
Mikal Bridges BKN - SG,SF


@BOS
2:30 am
19
-
8.2/17.5
.466
4.5/5.0
.891
2.3
23
4.5
2.8
1
0.5
1.8
Util
New Player Note
Scottie Barnes TOR - SF,PF


45
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Onyeka Okongwu ATL - C


115
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Bogdan Bogdanovic ATL - SG,SF,PF


177
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Drew Eubanks PHX - C


LAL
5:00 am
180
-
2.5/4.2
.586
1.1/1.3
.800
0
6
4.4
1.3
0.4
0.8
0.9
IL+
New Player Note
Nic Claxton BKN - C
INJ


@BOS
2:30 am
52
-
5.2/8.0
.653
1.3/2.2
.568
0
11.6
8.3
1.7
0.7
1.8
0.9
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoBronze level
 
Big O’s team 
Yonatan SINCE '23 View Profile
6-12-0
10th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 586 (-4)
Best Finish: N/A
Record: 0-2-0
Winning %: .000
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Tal's Top-Notch Team 4-14-0 11th
 
Week 2 Results
Loss 2 - 7
vs Earth is flat 🍟
 
Sat, Nov 11
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Big O’s team's Players roster for 2023-11-11.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
LaMelo Ball CHA - PG,SG


11
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
Austin Reaves LAL - SG,SF


107
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
G
New Player Note
Darius Garland CLE - PG


@GSW
3:30 am
36
-
7.4/16.5
.447
4.6/5.2
.888
2.3
21.6
2.9
7.3
1.4
0.1
3.8
SF
Player Note
Buddy Hield IND - SG,SF


96
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
Player Note
Keegan Murray SAC - SF,PF


Video Forecast
86
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
Player Note
Kelly Oubre Jr. PHI - SF


133
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Kevon Looney GSW - PF,C


CLE
3:30 am
141
-
2.8/4.7
.601
0.9/1.5
.639
0
6.6
9
2.4
0.8
0.6
1
C
New Player Note
Daniel Gafford WAS - PF,C
GTD


108
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
Mikal Bridges BKN - SG,SF


19
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
Scottie Barnes TOR - SF,PF


@BOS
2:00 am
45
-
6.3/13.3
.477
2.4/3.0
.779
1.2
16.2
8.2
4.4
1
1.3
2.5
BN
Player Note
Onyeka Okongwu ATL - C


MIA
2:30 am
115
-
3.5/5.3
.652
2.0/2.3
.844
0.2
9.1
6
1.3
0.6
0.9
0.9
BN
Player Note
Bogdan Bogdanovic ATL - SG,SF,PF


MIA
2:30 am
177
-
3.8/8.8
.429
0.7/0.7
.888
2.1
10.4
2.8
2.6
0.9
0.2
0.9
BN
Player Note
Drew Eubanks PHX - C


180
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
New Player Note
Nic Claxton BKN - C
INJ


52
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoBronze level
 
Big O’s team 
Yonatan SINCE '23 View Profile
6-12-0
10th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 586 (-4)
Best Finish: N/A
Record: 0-2-0
Winning %: .000
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Tal's Top-Notch Team 4-14-0 11th
 
Week 2 Results
Loss 2 - 7
vs Earth is flat 🍟
 
Sun, Nov 12
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Big O’s team's Players roster for 2023-11-12.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
LaMelo Ball CHA - PG,SG


@NYK
7:00 pm
11
-
6.9/17.5
.393
3.0/3.6
.849
3.2
20
5.8
8.6
1.1
0.3
3.1
SG
Player Note
Austin Reaves LAL - SG,SF


POR
5:00 am
107
-
5.1/11.3
.453
4.1/4.7
.875
1.6
16
3.6
4.2
0.9
0.3
2
G
New Player Note
Darius Garland CLE - PG


36
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Buddy Hield IND - SG,SF


@PHI
1:00 am
96
-
4.4/10.2
.430
0.6/0.8
.809
2.7
12.1
3.6
2.4
0.5
0.4
1.5
PF
Player Note
Keegan Murray SAC - SF,PF


Video Forecast
86
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
Player Note
Kelly Oubre Jr. PHI - SF


IND
1:00 am
133
-
6.6/13.9
.478
2.8/3.8
.727
2.9
19
4.9
1.1
1.4
0.5
1.1
C
Player Note
Kevon Looney GSW - PF,C


MIN
3:30 am
141
-
3.2/5.2
.608
1.1/1.8
.639
0
7.5
10.2
2.8
0.9
0.6
1.1
C
New Player Note
Daniel Gafford WAS - PF,C
GTD


@BKN
10:00 pm
108
-
4.2/6.3
.666
2.0/3.0
.667
0
10.4
7.4
0.9
0.4
1.4
1
Util
New Player Note
Mikal Bridges BKN - SG,SF


WAS
10:00 pm
19
-
8.3/17.5
.475
4.8/5.4
.891
2.3
23.8
4.4
3.1
1.1
0.6
1.8
Util
New Player Note
Scottie Barnes TOR - SF,PF


45
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Onyeka Okongwu ATL - C


115
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Bogdan Bogdanovic ATL - SG,SF,PF


177
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Drew Eubanks PHX - C


OKC
3:00 am
180
-
2.3/3.9
.599
1.3/1.7
.800
0
6
4.6
1.3
0.3
0.8
1.1
IL+
New Player Note
Nic Claxton BKN - C
INJ


WAS
10:00 pm
52
-
5.3/8.1
.655
1.3/2.4
.568
0
12
8.3
1.9
0.7
2.3
0.9
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved."""], "Tal": ["""Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoPlatinum level
 
Tal's Top-Notch Team 
Tal SINCE '20 View Profile
4-14-0
11th Place
 
Level: platinum LEVEL: PLATINUM 
Rating: 801 (-4)
Best Finish: Platinum (1x)
Record: 55-34-1
Winning %: .617
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Big O’s team 6-12-0 10th
 
Week 2 Results
Loss 1 - 8
vs Romshi's cum dumpsters
 
Mon, Nov 6
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Tal's Top-Notch Team's Players roster for 2023-11-06.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Jordan Clarkson UTA - PG,SG


@CHI
3:00 am
122
-
59%
6.7/15.4
.436
2.6/3.2
.810
2.5
18.5
4.5
5.1
0.7
0.2
2.9
SG
Player Note
Tyrese Haliburton IND - PG,SG


SAS
2:00 am
6
-
91%
7.6/15.2
.498
3.2/3.8
.838
2.5
20.9
4.7
9.9
1.7
0.5
2.7
G
Player Note
Fred VanVleet HOU - PG


SAC
3:00 am
35
-
88%
6.2/14.5
.427
3.3/3.7
.874
2.7
18.4
4.6
6.6
1.7
0.5
2.3
SF
Player Note
Paul George LAC - SG,SF,PF


@NYK
2:30 am
27
-
80%
7.4/16.3
.450
3.3/3.8
.855
2.8
20.8
6.2
3.7
1.3
0.4
2.5
PF
Player Note
Julius Randle NYK - PF


LAC
2:30 am
56
-
76%
7.8/17.2
.455
4.3/5.5
.770
2.6
22.5
9.7
3.6
0.6
0.3
2.6
F
Player Note
Kyle Kuzma WAS - SF,PF


@PHI
2:00 am
73
-
75%
6.2/13.1
.475
2.3/3.1
.731
1.6
16.3
6.9
2.7
0.4
0.5
2.1
C
New Player Note
Jalen Duren DET - C


Video Forecast
GSW
2:00 am
62
-
86%
3.8/5.8
.653
1.5/2.4
.628
0.1
9.1
8.9
1.2
0.6
0.6
1.3
C
Player Note
Goga Bitadze ORL - C


DAL
2:00 am
350
-
14%
1.8/3.2
.576
0.6/1.1
.577
0.2
4.5
4.1
0.9
0.3
0.7
0.6
Util
New Player Note
Zach Collins SAS - PF,C


@IND
2:00 am
104
-
73%
5.6/10.4
.540
2.3/3.0
.773
1
14.6
10.2
3.7
0.8
0.8
2.6
Util
Player Note
Dyson Daniels NOP - PG,SG


@DEN
4:00 am
341
-
8%
2.7/6.6
.415
0.9/1.2
.698
0.9
7.3
5.4
4
1.3
0.4
1.6
BN
Player Note
Ziaire Williams MEM - SF


354
-
5%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Dennis Schroder TOR - PG


92
-
31%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Eric Gordon PHX - SG,SF


Video Forecast
145
-
10%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Anfernee Simons POR - PG,SG
INJ


72
-
11%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Wendell Carter Jr. ORL - C
INJ


DAL
2:00 am
113
-
18%
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL+
New Player Note
Jamal Murray DEN - PG,SG
O


NOP
4:00 am
43
-
56%
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoPlatinum level
 
Tal's Top-Notch Team 
Tal SINCE '20 View Profile
4-14-0
11th Place
 
Level: platinum LEVEL: PLATINUM 
Rating: 801 (-4)
Best Finish: Platinum (1x)
Record: 55-34-1
Winning %: .617
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Big O’s team 6-12-0 10th
 
Week 2 Results
Loss 1 - 8
vs Romshi's cum dumpsters
 
Wed, Nov 8
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Tal's Top-Notch Team's Players roster for 2023-11-08.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Jordan Clarkson UTA - PG,SG


@IND
2:00 am
122
-
7.0/15.9
.443
3.0/3.6
.822
2.5
19.6
4.7
5.3
0.7
0.2
3
SG
Player Note
Tyrese Haliburton IND - PG,SG


UTA
2:00 am
6
-
7.3/15.1
.484
3.2/3.9
.837
2.5
20.3
4.6
9.4
1.6
0.5
2.7
G
Player Note
Fred VanVleet HOU - PG


LAL
3:00 am
35
-
6.1/14.7
.415
3.0/3.5
.870
2.7
17.9
4.5
6.5
1.6
0.5
2.2
SF
Player Note
Ziaire Williams MEM - SF


MIA
3:00 am
354
-
3.5/7.9
.447
0.9/1.2
.776
0.9
8.9
3.7
1.7
0.5
0.2
1.5
PF
Player Note
Paul George LAC - SG,SF,PF


@BKN
2:30 am
27
-
7.0/15.4
.451
3.1/3.7
.842
2.6
19.6
6
3.3
1.3
0.4
2.4
F
Player Note
Kyle Kuzma WAS - SF,PF


@CHA
2:00 am
73
-
6.4/13.6
.474
2.3/3.1
.745
1.6
16.8
7
2.8
0.4
0.5
2.1
C
New Player Note
Zach Collins SAS - PF,C


@NYK
2:30 am
104
-
5.3/10.2
.524
2.2/2.9
.758
1.1
14
9.3
3.7
0.8
0.7
2.5
C
New Player Note
Jalen Duren DET - C


Video Forecast
@MIL
3:00 am
62
-
4.3/6.9
.628
1.7/2.6
.643
0.1
10.5
10.2
1.3
0.8
0.8
1.4
Util
Player Note
Julius Randle NYK - PF


SAS
2:30 am
56
-
8.3/17.6
.470
4.4/5.8
.762
2.7
23.6
10.2
3.8
0.7
0.4
2.7
Util
Player Note
Dyson Daniels NOP - PG,SG


@MIN
3:00 am
341
-
2.9/6.9
.414
1.0/1.4
.694
1
7.7
5.8
4
1.3
0.4
1.7
BN
Player Note
Goga Bitadze ORL - C


350
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Dennis Schroder TOR - PG


@DAL
3:30 am
92
-
3.9/9.3
.421
2.9/3.4
.862
1.2
11.9
2.8
4.4
0.8
0.2
1.5
BN
New Player Note
Eric Gordon PHX - SG,SF


Video Forecast
@CHI
3:00 am
145
-
3.3/7.8
.424
1.2/1.5
.795
1.7
9.5
2.1
2.3
0.6
0.3
1.1
IL
Player Note
Anfernee Simons POR - PG,SG
INJ


@SAC
5:00 am
72
-
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL
Player Note
Wendell Carter Jr. ORL - C
INJ


113
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
New Player Note
Jamal Murray DEN - PG,SG
O


GSW
5:00 am
43
-
6.8/15.5
.439
2.8/3.4
.839
2.5
19
4.5
5.9
1.1
0.3
2.4
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoPlatinum level
 
Tal's Top-Notch Team 
Tal SINCE '20 View Profile
4-14-0
11th Place
 
Level: platinum LEVEL: PLATINUM 
Rating: 801 (-4)
Best Finish: Platinum (1x)
Record: 55-34-1
Winning %: .617
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Big O’s team 6-12-0 10th
 
Week 2 Results
Loss 1 - 8
vs Romshi's cum dumpsters
 
Thu, Nov 9
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Tal's Top-Notch Team's Players roster for 2023-11-09.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Jordan Clarkson UTA - PG,SG


122
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
Tyrese Haliburton IND - PG,SG


MIL
2:00 am
6
-
7.7/16.3
.473
3.2/3.7
.876
2.9
21.6
4
10.2
1.3
0.5
2.3
G
Player Note
Fred VanVleet HOU - PG


35
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Ziaire Williams MEM - SF


354
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
Player Note
Paul George LAC - SG,SF,PF


27
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
Player Note
Kyle Kuzma WAS - SF,PF


73
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
New Player Note
Jalen Duren DET - C


Video Forecast
62
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Goga Bitadze ORL - C


ATL
4:30 am
350
-
2.2/3.9
.563
1.4/1.9
.739
0.3
6
3.4
1.1
0.3
1
0.6
Util
Player Note
Julius Randle NYK - PF


56
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Dyson Daniels NOP - PG,SG


341
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Zach Collins SAS - PF,C


104
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Dennis Schroder TOR - PG


92
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Eric Gordon PHX - SG,SF


Video Forecast
145
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Anfernee Simons POR - PG,SG
INJ


72
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Wendell Carter Jr. ORL - C
INJ


ATL
4:30 am
113
-
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL+
New Player Note
Jamal Murray DEN - PG,SG
O


43
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoPlatinum level
 
Tal's Top-Notch Team 
Tal SINCE '20 View Profile
4-14-0
11th Place
 
Level: platinum LEVEL: PLATINUM 
Rating: 801 (-4)
Best Finish: Platinum (1x)
Record: 55-34-1
Winning %: .617
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Big O’s team 6-12-0 10th
 
Week 2 Results
Loss 1 - 8
vs Romshi's cum dumpsters
 
Fri, Nov 10
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Tal's Top-Notch Team's Players roster for 2023-11-10.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Jordan Clarkson UTA - PG,SG


@MEM
3:00 am
122
-
6.4/16.5
.391
2.7/3.3
.809
2.6
18.2
4.4
3.9
0.8
0.2
2.7
SG
New Player Note
Eric Gordon PHX - SG,SF


Video Forecast
LAL
5:00 am
145
-
4.4/10.0
.439
1.1/1.3
.838
2.1
11.9
2
2.4
0.6
0.3
1.3
G
Player Note
Fred VanVleet HOU - PG


NOP
3:00 am
35
-
6.0/15.8
.384
2.4/2.7
.898
3.4
18
3.8
7
1.3
0.4
2.4
SF
Player Note
Ziaire Williams MEM - SF


UTA
3:00 am
354
-
3.1/7.1
.438
0.9/1.1
.850
1.3
8.5
3.6
1.1
0.6
0.3
1
PF
Player Note
Paul George LAC - SG,SF,PF


@DAL
3:30 am
27
-
8.9/18.7
.476
4.8/5.4
.882
3.1
25.6
6.4
3.9
1.7
0.2
2.5
F
Player Note
Kyle Kuzma WAS - SF,PF


CHA
2:00 am
73
-
6.5/14.2
.456
2.3/3.0
.758
1.9
17.1
6.5
2.9
0.4
0.8
2
C
New Player Note
Jalen Duren DET - C


Video Forecast
PHI
2:00 am
62
-
5.9/8.9
.664
1.5/2.3
.654
0
13.3
10
2.4
0.7
1.4
2.3
C
New Player Note
Zach Collins SAS - PF,C


MIN
3:00 am
104
-
5.6/11.2
.500
2.0/2.8
.739
1
14.2
7.5
3.6
1
0.8
2.8
Util
Player Note
Julius Randle NYK - PF


56
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Dyson Daniels NOP - PG,SG


@HOU
3:00 am
341
-
3.5/7.8
.451
1.9/3.1
.619
1.1
10.1
5.3
4.2
1.6
1.4
1.4
BN
Player Note
Tyrese Haliburton IND - PG,SG


6
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Goga Bitadze ORL - C


350
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Dennis Schroder TOR - PG


92
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Anfernee Simons POR - PG,SG
INJ


72
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Wendell Carter Jr. ORL - C
INJ


113
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
New Player Note
Jamal Murray DEN - PG,SG
O


43
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoPlatinum level
 
Tal's Top-Notch Team 
Tal SINCE '20 View Profile
4-14-0
11th Place
 
Level: platinum LEVEL: PLATINUM 
Rating: 801 (-4)
Best Finish: Platinum (1x)
Record: 55-34-1
Winning %: .617
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Big O’s team 6-12-0 10th
 
Week 2 Results
Loss 1 - 8
vs Romshi's cum dumpsters
 
Sat, Nov 11
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Tal's Top-Notch Team's Players roster for 2023-11-11.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
New Player Note
Dennis Schroder TOR - PG


@BOS
2:00 am
92
-
4.9/11.3
.433
2.0/2.4
.815
1.4
13.1
2.9
5
0.7
0.1
1.7
SG
New Player Note
Eric Gordon PHX - SG,SF


Video Forecast
145
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
G
Player Note
Fred VanVleet HOU - PG


35
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Ziaire Williams MEM - SF


354
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
Player Note
Paul George LAC - SG,SF,PF


27
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
Player Note
Kyle Kuzma WAS - SF,PF


73
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
New Player Note
Zach Collins SAS - PF,C


104
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Goga Bitadze ORL - C


MIL
1:00 am
350
-
2.1/4.0
.525
1.3/1.8
.739
0.3
5.7
3.4
1.1
0.3
0.8
0.5
Util
Player Note
Julius Randle NYK - PF


56
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Dyson Daniels NOP - PG,SG


341
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Jordan Clarkson UTA - PG,SG


122
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Jalen Duren DET - C


Video Forecast
62
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Tyrese Haliburton IND - PG,SG


6
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Anfernee Simons POR - PG,SG
INJ


72
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Wendell Carter Jr. ORL - C
INJ


MIL
1:00 am
113
-
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL+
New Player Note
Jamal Murray DEN - PG,SG
O


43
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
Mucho Fantastico Fuego leago (ID# 114976)
Yahoo Sports Fantasy Basketball

Open chat
logoPlatinum level
 
Tal's Top-Notch Team 
Tal SINCE '20 View Profile
4-14-0
11th Place
 
Level: platinum LEVEL: PLATINUM 
Rating: 801 (-4)
Best Finish: Platinum (1x)
Record: 55-34-1
Winning %: .617
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Big O’s team 6-12-0 10th
 
Week 2 Results
Loss 1 - 8
vs Romshi's cum dumpsters
 
Sun, Nov 12
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Tal's Top-Notch Team's Players roster for 2023-11-12.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Tyrese Haliburton IND - PG,SG


@PHI
1:00 am
6
-
7.0/14.4
.483
3.4/3.9
.876
2.6
20
3.6
9.8
1.2
0.6
2.6
SG
New Player Note
Eric Gordon PHX - SG,SF


Video Forecast
OKC
3:00 am
145
-
4.3/9.5
.451
1.3/1.6
.838
2.1
12.1
2
2.5
0.5
0.4
1.7
G
Player Note
Fred VanVleet HOU - PG


DEN
2:00 am
35
-
5.9/15.2
.386
2.3/2.6
.898
3.1
17.2
3.6
7
1.3
0.3
2.1
SF
Player Note
Ziaire Williams MEM - SF


@LAC
10:30 pm
354
-
3.0/6.7
.442
0.9/1.0
.849
1.2
8
3.6
1.1
0.6
0.3
1
PF
Player Note
Paul George LAC - SG,SF,PF


MEM
10:30 pm
27
-
9.3/20.6
.452
4.7/5.3
.882
3.8
27.1
6.6
4.4
1.9
0.3
3
F
Player Note
Kyle Kuzma WAS - SF,PF


@BKN
10:00 pm
73
-
6.0/13.5
.443
2.2/2.9
.758
1.8
16
6.1
2.6
0.4
0.5
1.8
C
New Player Note
Zach Collins SAS - PF,C


MIA
2:00 am
104
-
5.1/10.0
.512
1.6/2.2
.739
1.1
12.9
6.8
3.6
0.8
0.7
2.7
C
New Player Note
Jalen Duren DET - C


Video Forecast
@CHI
2:00 am
62
-
5.8/8.8
.657
1.4/2.2
.654
0
13
10.8
2.6
0.7
1.5
2.5
Util
Player Note
Julius Randle NYK - PF


CHA
7:00 pm
56
-
7.2/17.9
.404
4.5/6.4
.713
2.2
21.2
10.9
4.4
0.8
0.5
3.3
Util
Player Note
Dyson Daniels NOP - PG,SG


DAL
2:00 am
341
-
3.4/7.5
.456
1.9/3.1
.619
0.8
9.5
5.5
3.8
1.1
0.8
1.4
BN
New Player Note
Dennis Schroder TOR - PG


92
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Goga Bitadze ORL - C


350
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Jordan Clarkson UTA - PG,SG


122
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL
Player Note
Anfernee Simons POR - PG,SG
INJ


@LAL
5:00 am
72
-
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
IL
Player Note
Wendell Carter Jr. ORL - C
INJ


113
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
New Player Note
Jamal Murray DEN - PG,SG
O


@HOU
2:00 am
43
-
7.5/16.2
.464
3.0/3.5
.857
3.2
21.2
3.5
7.3
0.9
0.6
2.2
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved."""],
        "Tani_2": ["""Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
9-8-1
4th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 567 (+8)
Best Finish: Bronze (1x)
Record: 8-13-1
Winning %: .386
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Noodles boys 10-8-0 2nd
 
Week 2 Results
Tie 4 - 4
vs theUchiha

You have used 0 of your 5 player adds for this week.

You have used 0 of 3 IL positions and 1 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Mon, Nov 6
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-06.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Fred VanVleet HOU - PG
SAC
3:00 am
35
-
86%
6.2/14.6
.427
3.3/3.8
.874
2.7
18.5
4.6
6.6
1.7
0.5
2.3
SG
New Player Note
Shai Gilgeous-Alexander OKC - PG,SG
O
ATL
3:00 am
5
-
54%
0.0/0.0
.000
0.0/0.0
.000
0
0
0
0
0
0
0
G
Player Note
T.J. McConnell IND - PG
SAS
2:00 am
208
-
3%
0.6/1.1
.533
0.1/0.2
.819
0.1
1.4
0.6
0.7
0.2
0
0.3
SF
New Player Note
LeBron James LAL - SF,PF
@MIA
2:30 am
29
-
91%
9.0/18.8
.475
3.3/4.4
.749
2.1
23.3
8.8
6.1
0.9
0.5
2.8
PF
Player Note
Brandon Ingram NOP - SG,SF,PF
@DEN
4:00 am
51
-
70%
7.7/16.2
.477
4.2/4.8
.867
1.5
21.1
5.7
5.3
0.8
0.5
2.9
F
No new player Notes
Kyle Anderson MIN - SF,PF
BOS
3:00 am
159
-
23%
3.3/6.7
.484
1.2/1.6
.749
0.7
8.3
4.6
3.3
1
0.6
1.2
C
Player Note
Kevon Looney GSW - PF,C
@DET
2:00 am
141
-
58%
3.4/5.4
.638
1.6/2.6
.633
0
8.5
10.5
2.3
0.6
0.7
0.8
Util
New Player Note
Patrick Williams CHI - PF
GTD
UTA
3:00 am
157
-
15%
3.1/6.7
.457
1.0/1.2
.818
1.1
8.2
3.3
1.1
0.7
0.6
1
Util
Player Note
Buddy Hield IND - SG,SF
SAS
2:00 am
96
-
68%
4.8/10.2
.471
1.2/1.5
.792
2.5
13.3
4.7
2.3
1
0.3
1.5
Util
Player Note
Rudy Gobert MIN - C
BOS
3:00 am
69
-
86%
5.0/8.0
.625
2.7/4.2
.656
0.1
12.8
11.6
1.2
0.8
1.2
1.7
BN
Player Note
Pascal Siakam TOR - PF,C
Video Forecast
33
-
62%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Malcolm Brogdon POR - PG,SG
110
-
36%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Kevin Durant PHX - SF,PF
12
-
62%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
No new player Notes
Ja Morant MEM - PG
O
81
-
20%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
9-8-1
  |  
4th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
There are no sit/start suggestions available right now. Check back later!
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
9-8-1
4th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 567 (+8)
Best Finish: Bronze (1x)
Record: 8-13-1
Winning %: .386
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Noodles boys 10-8-0 2nd
 
Week 2 Results
Tie 4 - 4
vs theUchiha

You have used 0 of your 5 player adds for this week.

You have used 0 of 3 IL positions and 1 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Wed, Nov 8
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-08.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Fred VanVleet HOU - PG
LAL
3:00 am
35
-
6.1/14.7
.415
3.0/3.5
.870
2.7
17.9
4.5
6.5
1.6
0.5
2.2
SG
New Player Note
Shai Gilgeous-Alexander OKC - PG,SG
O
CLE
3:00 am
5
-
8.8/17.6
.498
7.4/8.4
.881
1
25.9
5.2
5
1.5
0.7
2.5
G
Player Note
T.J. McConnell IND - PG
UTA
2:00 am
208
-
0.6/1.1
.522
0.1/0.2
.814
0.1
1.4
0.5
0.7
0.2
0
0.3
SF
New Player Note
LeBron James LAL - SF,PF
@HOU
3:00 am
29
-
8.5/17.9
.476
3.3/4.4
.753
2.1
22.4
8.2
5.9
0.9
0.5
2.6
PF
Player Note
Brandon Ingram NOP - SG,SF,PF
@MIN
3:00 am
51
-
7.9/16.7
.474
4.5/5.2
.863
1.6
22
6
5.3
0.8
0.5
3
F
No new player Notes
Kyle Anderson MIN - SF,PF
NOP
3:00 am
159
-
3.2/6.6
.488
1.3/1.7
.755
0.7
8.4
4.7
3.5
1
0.7
1.2
C
Player Note
Kevon Looney GSW - PF,C
@DEN
5:00 am
141
-
3.4/5.5
.618
1.5/2.4
.635
0.1
8.4
10.2
2.3
0.6
0.7
0.8
Util
New Player Note
Patrick Williams CHI - PF
GTD
PHX
3:00 am
157
-
3.0/6.5
.452
1.0/1.2
.827
1
8
3.4
1.1
0.7
0.6
1
Util
Player Note
Buddy Hield IND - SG,SF
UTA
2:00 am
96
-
4.6/10.1
.453
1.3/1.6
.805
2.5
12.9
4.7
2.2
0.9
0.3
1.5
Util
Player Note
Rudy Gobert MIN - C
NOP
3:00 am
69
-
5.0/7.8
.643
2.9/4.4
.662
0.1
13.1
11.7
1.3
0.8
1.2
1.7
BN
Player Note
Pascal Siakam TOR - PF,C
Video Forecast
@DAL
3:30 am
33
-
7.4/15.2
.484
4.2/5.4
.782
1.3
20.2
7.9
4.8
0.9
0.5
1.9
BN
New Player Note
Malcolm Brogdon POR - PG,SG
@SAC
5:00 am
110
-
6.2/13.1
.475
3.1/3.6
.877
2.7
18.3
5.1
5.1
0.8
0.3
1.8
BN
New Player Note
Kevin Durant PHX - SF,PF
@CHI
3:00 am
12
-
8.2/15.8
.518
4.1/4.7
.874
1.9
22.4
7.8
4.5
0.8
1.2
2.7
IL+
No new player Notes
Ja Morant MEM - PG
O
MIA
3:00 am
81
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
9-8-1
  |  
4th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Photo of Malcolm BrogdonPhoto of T.J. McConnell
Malcolm Brogdon
T.J. McConnell
Compare
Photo of Kevin DurantPhoto of Brandon Ingram
Kevin Durant
Brandon Ingram
Compare
Photo of Pascal SiakamPhoto of Kyle Anderson
Pascal Siakam
Kyle Anderson
Compare
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
9-8-1
4th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 567 (+8)
Best Finish: Bronze (1x)
Record: 8-13-1
Winning %: .386
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Noodles boys 10-8-0 2nd
 
Week 2 Results
Tie 4 - 4
vs theUchiha

You have used 0 of your 5 player adds for this week.

You have used 0 of 3 IL positions and 1 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Thu, Nov 9
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-09.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Fred VanVleet HOU - PG
35
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
New Player Note
Shai Gilgeous-Alexander OKC - PG,SG
O
5
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
G
Player Note
T.J. McConnell IND - PG
MIL
2:00 am
208
-
0.5/1.1
.477
0.1/0.1
.860
0
1.1
0.4
0.6
0.1
0
0.1
SF
New Player Note
LeBron James LAL - SF,PF
29
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
Player Note
Brandon Ingram NOP - SG,SF,PF
51
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
No new player Notes
Kyle Anderson MIN - SF,PF
159
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Kevon Looney GSW - PF,C
141
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
Patrick Williams CHI - PF
GTD
157
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Buddy Hield IND - SG,SF
MIL
2:00 am
96
-
4.8/11.3
.429
0.6/0.7
.810
3
13.3
4
2.5
0.6
0.3
1.3
Util
Player Note
Rudy Gobert MIN - C
69
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Pascal Siakam TOR - PF,C
Video Forecast
33
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Malcolm Brogdon POR - PG,SG
110
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Kevin Durant PHX - SF,PF
12
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
No new player Notes
Ja Morant MEM - PG
O
81
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
9-8-1
  |  
4th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
There are no sit/start suggestions available right now. Check back later!
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
9-8-1
4th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 567 (+8)
Best Finish: Bronze (1x)
Record: 8-13-1
Winning %: .386
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Noodles boys 10-8-0 2nd
 
Week 2 Results
Tie 4 - 4
vs theUchiha

You have used 0 of your 5 player adds for this week.

You have used 0 of 3 IL positions and 1 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Fri, Nov 10
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-10.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Fred VanVleet HOU - PG
NOP
3:00 am
35
-
6.0/15.8
.384
2.4/2.7
.898
3.4
18
3.8
7
1.3
0.4
2.4
SG
New Player Note
Shai Gilgeous-Alexander OKC - PG,SG
O
@SAC
5:00 am
5
-
10.5/21.0
.501
7.7/8.7
.886
1.2
29.9
5.3
6.2
1.8
0.7
2.8
G
Player Note
T.J. McConnell IND - PG
208
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
New Player Note
LeBron James LAL - SF,PF
@PHX
5:00 am
29
-
8.7/17.4
.498
4.3/6.0
.720
2.1
23.7
7.9
5.6
1.1
0.6
3.5
PF
Player Note
Brandon Ingram NOP - SG,SF,PF
@HOU
3:00 am
51
-
7.8/15.8
.492
4.9/5.7
.859
1.6
22.1
5.5
5.3
0.7
0.5
2.6
F
No new player Notes
Kyle Anderson MIN - SF,PF
@SAS
3:00 am
159
-
3.7/7.0
.537
1.3/1.7
.767
0.4
9.2
4.4
4
1.2
1
1.2
C
Player Note
Kevon Looney GSW - PF,C
141
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Buddy Hield IND - SG,SF
96
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Rudy Gobert MIN - C
@SAS
3:00 am
69
-
5.6/8.7
.643
3.4/5.1
.677
0
14.7
12.6
1.1
0.9
2.1
1.6
Util
New Player Note
Kevin Durant PHX - SF,PF
LAL
5:00 am
12
-
10.3/20.2
.510
5.6/6.5
.856
1.7
27.9
6.7
5.2
0.8
1.1
3.1
BN
New Player Note
Patrick Williams CHI - PF
GTD
157
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Pascal Siakam TOR - PF,C
Video Forecast
33
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Malcolm Brogdon POR - PG,SG
110
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
No new player Notes
Ja Morant MEM - PG
O
UTA
3:00 am
81
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
9-8-1
  |  
4th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
There are no sit/start suggestions available right now. Check back later!
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
9-8-1
4th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 567 (+8)
Best Finish: Bronze (1x)
Record: 8-13-1
Winning %: .386
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Noodles boys 10-8-0 2nd
 
Week 2 Results
Tie 4 - 4
vs theUchiha

You have used 0 of your 5 player adds for this week.

You have used 0 of 3 IL positions and 1 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Sat, Nov 11
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-11.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Fred VanVleet HOU - PG
35
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
New Player Note
Shai Gilgeous-Alexander OKC - PG,SG
O
5
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
G
Player Note
T.J. McConnell IND - PG
208
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
New Player Note
LeBron James LAL - SF,PF
29
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
Player Note
Pascal Siakam TOR - PF,C
Video Forecast
@BOS
2:00 am
33
-
6.8/14.9
.455
2.8/3.6
.765
1.1
17.4
6.8
4.1
0.8
0.3
1.9
F
No new player Notes
Kyle Anderson MIN - SF,PF
159
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
Player Note
Kevon Looney GSW - PF,C
CLE
3:30 am
141
-
2.8/4.7
.601
0.9/1.5
.639
0
6.6
9
2.4
0.8
0.6
1
Util
Player Note
Buddy Hield IND - SG,SF
96
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Rudy Gobert MIN - C
69
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
Kevin Durant PHX - SF,PF
12
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Brandon Ingram NOP - SG,SF,PF
51
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Patrick Williams CHI - PF
GTD
157
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Malcolm Brogdon POR - PG,SG
110
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
IL+
No new player Notes
Ja Morant MEM - PG
O
81
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
9-8-1
  |  
4th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
Start Player
Sit Player
Compare
There are no sit/start suggestions available right now. Check back later!
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoBronze level
 
TheRealTani 
Jonathan SINCE '22 View Profile
9-8-1
4th Place
 
Level: bronze LEVEL: BRONZE 
Rating: 567 (+8)
Best Finish: Bronze (1x)
Record: 8-13-1
Winning %: .386
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs Noodles boys 10-8-0 2nd
 
Week 2 Results
Tie 4 - 4
vs theUchiha

You have used 0 of your 5 player adds for this week.

You have used 0 of 3 IL positions and 1 of 1 IL+ positions on your roster.

You have received one or more medals in the last day. Go to your fantasy profile to view them.View Details 
 
Sun, Nov 12
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Add Player Drop Player Research Assistant Create Trade Compare My Team
TheRealTani's Players roster for 2023-11-12.
Details
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Fred VanVleet HOU - PG
DEN
2:00 am
35
-
5.9/15.2
.386
2.3/2.6
.898
3.1
17.2
3.6
7
1.3
0.3
2.1
SG
New Player Note
Shai Gilgeous-Alexander OKC - PG,SG
O
@PHX
3:00 am
5
-
9.5/20.0
.473
8.3/9.3
.886
1.1
28.3
5.2
5.3
1.7
0.7
2.7
G
Player Note
T.J. McConnell IND - PG
@PHI
1:00 am
208
-
0.5/0.9
.503
0.1/0.1
.852
0
1
0.4
0.6
0.1
0
0.1
SF
New Player Note
LeBron James LAL - SF,PF
POR
5:00 am
29
-
9.1/17.3
.524
4.0/5.5
.720
2.2
24.3
7.8
6.4
1.1
0.6
3.2
PF
New Player Note
Patrick Williams CHI - PF
GTD
DET
2:00 am
157
-
2.6/5.7
.452
1.7/2.1
.811
0.6
7.5
3.7
1
0.9
0.6
0.9
F
No new player Notes
Kyle Anderson MIN - SF,PF
@GSW
3:30 am
159
-
3.4/6.8
.497
1.4/1.8
.766
0.5
8.5
4.3
3.8
1.2
0.8
1.2
C
Player Note
Kevon Looney GSW - PF,C
MIN
3:30 am
141
-
3.2/5.2
.608
1.1/1.8
.639
0
7.5
10.2
2.8
0.9
0.6
1.1
Util
Player Note
Buddy Hield IND - SG,SF
@PHI
1:00 am
96
-
4.4/10.2
.430
0.6/0.8
.809
2.7
12.1
3.6
2.4
0.5
0.4
1.5
Util
Player Note
Rudy Gobert MIN - C
@GSW
3:30 am
69
-
5.0/8.2
.602
3.7/5.4
.677
0
13.6
12.3
1.1
0.9
1.6
1.7
Util
New Player Note
Kevin Durant PHX - SF,PF
OKC
3:00 am
12
-
9.8/18.9
.522
6.9/8.1
.856
1.7
28.3
6.9
5.3
0.8
1.2
4.1
BN
Player Note
Pascal Siakam TOR - PF,C
Video Forecast
33
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Brandon Ingram NOP - SG,SF,PF
DAL
2:00 am
51
-
7.7/15.7
.493
4.9/5.7
.859
1.2
21.6
5.9
4.9
0.5
0.3
2.5
BN
New Player Note
Malcolm Brogdon POR - PG,SG
@LAL
5:00 am
110
-
6.4/15.3
.417
2.6/3.1
.836
1.9
17.2
5
5.6
0.9
0.2
1.7
IL+
No new player Notes
Ja Morant MEM - PG
O
@LAC
10:30 pm
81
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
 
 
Roster Edit Mode:  Swap Mode  Classic Mode
 
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats
Team analysis

Find the best moves for your team
|
Hide
TheRealTani logoTheRealTani tier: bronze
TheRealTani
9-8-1
  |  
4th Place
  |  
Jonathan
Strengths
Neutral
Weaknesses
Unlock your team's positional strengths and more!
Try 7 days free
Fantasy Plus logo
Research Assistant  |  
Trade Hub
Sit/start suggestions
Add/drop suggestions
Trade suggestions
Photo of Brandon IngramPhoto of T.J. McConnell
Brandon Ingram
T.J. McConnell
Compare
Note To Self
Use the Note To Self area to jot player notes, write reminders, create lists, or store frequently used text.

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved."""], "Omer": ["""Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoSilver level
 
Noodles boys 
Omer SINCE '18 View Profile
10-8-0
2nd Place
 
Level: silver LEVEL: SILVER 
Rating: 661 (-10)
Best Finish: Silver (5x)
Record: 55-42-5
Winning %: .564
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 9-8-1 4th
 
Week 2 Results
Won 7 - 2
vs הבית של מיץ פלטל 2.0
 
Mon, Nov 6
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Noodles boys's Players roster for 2023-11-06.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Damian Lillard MIL - PG


@BKN
2:30 am
10
-
82%
7.5/16.2
.460
5.8/6.5
.889
3
23.8
4.7
6.4
0.9
0.3
2.9
SG
Player Note
Tyler Herro MIA - PG,SG


LAL
2:30 am
59
-
76%
7.3/16.8
.435
2.2/2.4
.881
3.1
19.8
5.6
3.9
0.8
0.3
2.4
G
Player Note
Austin Reaves LAL - SG,SF


@MIA
2:30 am
107
-
69%
4.2/8.5
.493
2.8/3.4
.841
1.7
12.9
3.7
3.6
0.7
0.3
1.6
SF
Player Note
Malik Monk SAC - SG,SF


@HOU
3:00 am
138
-
34%
5.3/11.7
.455
2.7/3.1
.881
2.1
15.5
3.4
4.3
0.8
0.3
2.1
PF
Player Note
Lauri Markkanen UTA - SF,PF


@CHI
3:00 am
25
-
91%
7.5/15.4
.488
4.0/4.7
.854
2.8
21.9
9.3
2.1
0.7
0.5
1.9
F
Player Note
Jalen Johnson ATL - SF,PF


Video Forecast
@OKC
3:00 am
117
-
58%
4.5/9.2
.485
1.5/2.3
.648
1
11.5
8.6
2.3
1
1
1.3
C
New Player Note
Anthony Davis LAL - PF,C


@MIA
2:30 am
9
-
92%
7.7/14.2
.545
4.4/5.7
.765
0.4
20.2
13.2
2.5
1
1.5
2
Util
New Player Note
Moritz Wagner ORL - C


DAL
2:00 am
271
-
21%
4.8/9.2
.524
3.2/3.9
.828
1.2
14
7.6
1.7
0.7
0.4
1.5
Util
New Player Note
Paolo Banchero ORL - SF,PF


Video Forecast
DAL
2:00 am
66
-
83%
6.6/14.6
.451
4.7/6.2
.747
1.3
19.2
8.1
3.1
0.7
0.6
2.5
Util
Player Note
Chet Holmgren OKC - PF,C


ATL
3:00 am
38
-
79%
6.4/12.8
.504
3.3/4.3
.750
1.8
18
10.4
2.2
0.9
2
2.2
BN
New Player Note
Darius Garland CLE - PG


36
-
49%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Shaedon Sharpe POR - SG,SF


116
-
39%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
OG Anunoby TOR - SG,SF


49
-
57%
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoSilver level
 
Noodles boys 
Omer SINCE '18 View Profile
10-8-0
2nd Place
 
Level: silver LEVEL: SILVER 
Rating: 661 (-10)
Best Finish: Silver (5x)
Record: 55-42-5
Winning %: .564
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 9-8-1 4th
 
Week 2 Results
Won 7 - 2
vs הבית של מיץ פלטל 2.0
 
Wed, Nov 8
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Noodles boys's Players roster for 2023-11-08.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Damian Lillard MIL - PG


DET
3:00 am
10
-
7.5/16.0
.469
5.9/6.6
.890
3
24
4.7
6.6
0.9
0.3
2.9
SG
Player Note
Tyler Herro MIA - PG,SG


@MEM
3:00 am
59
-
7.2/16.5
.434
2.3/2.6
.884
3.2
19.8
5.7
4.1
0.8
0.3
2.5
G
Player Note
Austin Reaves LAL - SG,SF


@HOU
3:00 am
107
-
4.2/8.5
.495
3.0/3.5
.849
1.7
13.2
3.6
3.6
0.7
0.3
1.5
SF
Player Note
Malik Monk SAC - SG,SF


POR
5:00 am
138
-
4.0/8.9
.450
1.9/2.2
.881
1.7
11.6
2.7
3.3
0.6
0.2
1.6
PF
Player Note
Lauri Markkanen UTA - SF,PF


@IND
2:00 am
25
-
7.9/15.9
.499
4.4/5.1
.860
2.8
23
9.6
2.3
0.7
0.5
1.9
F
New Player Note
Shaedon Sharpe POR - SG,SF


@SAC
5:00 am
116
-
6.3/13.8
.457
1.9/2.5
.747
2.6
17.1
5
2.5
0.8
0.4
1.8
C
New Player Note
Anthony Davis LAL - PF,C


@HOU
3:00 am
9
-
8.4/15.5
.543
5.2/6.8
.769
0.4
22.5
14.5
2.9
1.2
1.8
2.2
Util
Player Note
Chet Holmgren OKC - PF,C


CLE
3:00 am
38
-
4.8/9.9
.481
1.9/2.7
.703
1.7
13.1
8.9
1.7
0.7
1.6
1.8
Util
New Player Note
Darius Garland CLE - PG


@OKC
3:00 am
36
-
6.7/14.6
.457
3.8/4.4
.846
2
19.1
3.5
7.3
1.2
0.2
3
Util
New Player Note
OG Anunoby TOR - SG,SF


@DAL
3:30 am
49
-
5.5/11.7
.474
1.9/2.3
.837
2
15
5.1
1.9
1.7
0.7
1.6
BN
Player Note
Jalen Johnson ATL - SF,PF


Video Forecast
117
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Moritz Wagner ORL - C


271
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Paolo Banchero ORL - SF,PF


Video Forecast
66
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoSilver level
 
Noodles boys 
Omer SINCE '18 View Profile
10-8-0
2nd Place
 
Level: silver LEVEL: SILVER 
Rating: 661 (-10)
Best Finish: Silver (5x)
Record: 55-42-5
Winning %: .564
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 9-8-1 4th
 
Week 2 Results
Won 7 - 2
vs הבית של מיץ פלטל 2.0
 
Thu, Nov 9
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Noodles boys's Players roster for 2023-11-09.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Damian Lillard MIL - PG


@IND
2:00 am
10
-
8.4/17.8
.474
8.2/9.0
.919
3.6
28.7
5.2
7.1
1
0.4
3.2
SG
Player Note
Tyler Herro MIA - PG,SG


59
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
G
Player Note
Austin Reaves LAL - SG,SF


107
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Jalen Johnson ATL - SF,PF


Video Forecast
@ORL
4:30 am
117
-
5.3/9.6
.552
1.4/2.1
.645
1
12.9
7.7
2.6
1.3
1.1
1.5
PF
New Player Note
Paolo Banchero ORL - SF,PF


Video Forecast
ATL
4:30 am
66
-
7.6/16.5
.465
5.4/7.6
.712
1.4
22.1
7.2
4.8
1.1
0.8
3.3
F
New Player Note
Shaedon Sharpe POR - SG,SF


116
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
New Player Note
Moritz Wagner ORL - C


ATL
4:30 am
271
-
5.8/10.7
.542
2.6/3.3
.790
1.5
15.7
6.4
2.1
0.6
0.7
1.6
Util
Player Note
Chet Holmgren OKC - PF,C


38
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
Darius Garland CLE - PG


36
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
OG Anunoby TOR - SG,SF


49
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Malik Monk SAC - SG,SF


138
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Lauri Markkanen UTA - SF,PF


25
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Anthony Davis LAL - PF,C


9
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoSilver level
 
Noodles boys 
Omer SINCE '18 View Profile
10-8-0
2nd Place
 
Level: silver LEVEL: SILVER 
Rating: 661 (-10)
Best Finish: Silver (5x)
Record: 55-42-5
Winning %: .564
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 9-8-1 4th
 
Week 2 Results
Won 7 - 2
vs הבית של מיץ פלטל 2.0
 
Fri, Nov 10
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Noodles boys's Players roster for 2023-11-10.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Damian Lillard MIL - PG


10
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
Malik Monk SAC - SG,SF


OKC
5:00 am
138
-
3.5/7.9
.444
1.3/1.6
.842
1.8
10.2
2.5
2.6
0.4
0.5
1.5
G
Player Note
Austin Reaves LAL - SG,SF


@PHX
5:00 am
107
-
4.8/11.1
.429
4.3/4.9
.875
1.5
15.3
3.6
3.6
0.8
0.3
2.1
SF
Player Note
Lauri Markkanen UTA - SF,PF


@MEM
3:00 am
25
-
8.5/18.6
.460
4.4/5.1
.865
3.6
25
8.8
1.9
0.8
0.6
1.3
PF
New Player Note
Paolo Banchero ORL - SF,PF


Video Forecast
66
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
F
New Player Note
Shaedon Sharpe POR - SG,SF


116
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
New Player Note
Anthony Davis LAL - PF,C


@PHX
5:00 am
9
-
9.7/18.1
.536
5.9/7.3
.808
0.4
25.7
12.9
2.6
1.3
2.3
2.1
Util
Player Note
Chet Holmgren OKC - PF,C


@SAC
5:00 am
38
-
5.5/10.3
.532
2.5/3.3
.761
1.9
15.4
7.4
2.2
0.9
2
2.1
Util
New Player Note
Darius Garland CLE - PG


36
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
OG Anunoby TOR - SG,SF


49
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Tyler Herro MIA - PG,SG


59
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Jalen Johnson ATL - SF,PF


Video Forecast
117
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Moritz Wagner ORL - C


271
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoSilver level
 
Noodles boys 
Omer SINCE '18 View Profile
10-8-0
2nd Place
 
Level: silver LEVEL: SILVER 
Rating: 661 (-10)
Best Finish: Silver (5x)
Record: 55-42-5
Winning %: .564
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 9-8-1 4th
 
Week 2 Results
Won 7 - 2
vs הבית של מיץ פלטל 2.0
 
Sat, Nov 11
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Noodles boys's Players roster for 2023-11-11.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Damian Lillard MIL - PG


@ORL
1:00 am
10
-
7.8/17.0
.458
7.1/7.7
.919
3.6
26.2
4.7
6.7
0.9
0.3
3
SG
Player Note
Tyler Herro MIA - PG,SG


@ATL
2:30 am
59
-
9.4/20.8
.453
3.0/3.3
.905
3.5
25.3
5.6
4.7
0.9
0.1
2.7
G
Player Note
Austin Reaves LAL - SG,SF


107
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SF
Player Note
Jalen Johnson ATL - SF,PF


Video Forecast
MIA
2:30 am
117
-
5.0/9.0
.555
1.2/1.9
.645
0.9
12.1
7.6
2.5
1.1
0.8
1.6
PF
New Player Note
Paolo Banchero ORL - SF,PF


Video Forecast
MIL
1:00 am
66
-
7.4/17.0
.434
5.0/7.0
.712
1.4
21.2
7.2
4.4
1.1
0.6
2.8
F
New Player Note
Shaedon Sharpe POR - SG,SF


116
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
C
New Player Note
Moritz Wagner ORL - C


MIL
1:00 am
271
-
5.6/11.0
.511
2.4/3.0
.791
1.5
15.1
6.4
1.9
0.5
0.5
1.4
Util
Player Note
Chet Holmgren OKC - PF,C


38
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
Darius Garland CLE - PG


@GSW
3:30 am
36
-
7.4/16.5
.447
4.6/5.2
.888
2.3
21.6
2.9
7.3
1.4
0.1
3.8
Util
New Player Note
OG Anunoby TOR - SG,SF


@BOS
2:00 am
49
-
6.0/12.6
.476
1.3/1.8
.744
2.2
15.6
4.8
2
1.4
0.5
1.4
BN
Player Note
Malik Monk SAC - SG,SF


138
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Lauri Markkanen UTA - SF,PF


25
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Anthony Davis LAL - PF,C


9
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved.""", """Yahoo Sports
Yahoo Sports
Search query
Search

News
Finance
Sports

More

J
 Fantasy Basketball
Overview
League
My Team
Matchups
Players
Research
Draft
StatTracker
Plus Yahoo Fantasy Plus
…
Sports
Fantasy
Daily Fantasy
שוכחים את שניוק האמיתי (ID# 2540)
Yahoo Sports Fantasy Basketball

Open chat

logoSilver level
 
Noodles boys 
Omer SINCE '18 View Profile
10-8-0
2nd Place
 
Level: silver LEVEL: SILVER 
Rating: 661 (-10)
Best Finish: Silver (5x)
Record: 55-42-5
Winning %: .564
 
WEEK 3 MATCHUP
logo
 
0
vs	
0
 
logo
vs TheRealTani 9-8-1 4th
 
Week 2 Results
Won 7 - 2
vs הבית של מיץ פלטל 2.0
 
Sun, Nov 12
  
Stats
 
Advanced Stats Fantasy Plus Logo
 
Projected Stats
 
Average Stats
 
Standard Deviations
 
Split Stats
 
Ranks
 
Opponents
 
Research
 
Matchup Ratings
Today
 
Remaining Games
Create Trade Compare My Team
Noodles boys's Players roster for 2023-11-12.
 
 
 
 
 
Rankings
Fantasy
Field Goals
Free Throws
3PT
 
Pos
Players
Action
Forecast
Opp
Status
Pre-Season
Current
% Started
FGM/A*
FG%
FTM/A*
FT%
3PTM
PTS
REB
AST
ST
BLK
TO
PG
Player Note
Damian Lillard MIL - PG


10
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
SG
Player Note
Tyler Herro MIA - PG,SG


@SAS
2:00 am
59
-
10.0/21.1
.472
3.1/3.5
.905
3.6
26.7
5.7
4.9
1
0.1
2.7
G
Player Note
Austin Reaves LAL - SG,SF


POR
5:00 am
107
-
5.1/11.3
.453
4.1/4.7
.875
1.6
16
3.6
4.2
0.9
0.3
2
SF
Player Note
Jalen Johnson ATL - SF,PF


Video Forecast
117
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
PF
New Player Note
Anthony Davis LAL - PF,C


POR
5:00 am
9
-
9.6/16.9
.565
5.2/6.4
.808
0.4
24.7
12.1
2.8
1.3
2.3
1.8
F
New Player Note
Shaedon Sharpe POR - SG,SF


@LAL
5:00 am
116
-
7.3/16.3
.449
2.5/3.3
.756
2.5
19.6
5.7
2.9
1.1
0.9
2.2
C
New Player Note
Moritz Wagner ORL - C


271
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
Player Note
Chet Holmgren OKC - PF,C


@PHX
3:00 am
38
-
4.9/9.7
.508
2.7/3.5
.761
1.7
14.3
7.3
1.9
0.8
1.8
2.1
Util
New Player Note
Darius Garland CLE - PG


36
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Util
New Player Note
OG Anunoby TOR - SG,SF


49
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
New Player Note
Paolo Banchero ORL - SF,PF


Video Forecast
66
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Malik Monk SAC - SG,SF


138
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
BN
Player Note
Lauri Markkanen UTA - SF,PF


25
-
-/-
.000
-/-
.000
0
0
0
0
0
0
0
Legends and Glossaries
Legend

Stats

Positions

Advanced Stats Glossary

The Fine Print
Projections Powered by Rotowire
Stat corrections are applied on Monday, Nov 13.
All game times are shown in IST.
* Non-scoring stats

Yahoo Sports - NBC Sports Network - Paid Fantasy Terms - Feedback - Terms and Privacy Policy - Privacy Dashboard  - About Our Ads - Help
Certain Data by Sportradar and Rotowire

The NBA identifications are the intellectual property of NBA Properties, Inc. © 2023 NBA Properties, Inc. All Rights Reserved.

© 2023 Yahoo Fantasy Sports LLC. All rights reserved."""]
    }
    all_teams_data = {name: {} for name in all_teams_text.keys()}
    for team_name, team_text_list in all_teams_text.items():
        for i, team_text in enumerate(team_text_list):
            team_stats, stats_date = fetch_team_data(team_name, team_text)
            sorted_stats_by_player = team_stats.sort_values(by=f"{team_name} - Players")
            all_teams_data[team_name][stats_date] = sorted_stats_by_player

    param_cols = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'ST', 'BLK', 'TO']
    pre_weekly_stats = {name: list(all_teams_data[name].values())[0].copy() for name in all_teams_data.keys()}
    weekly_stats = {}
    for name, df in pre_weekly_stats.copy().items():
        df.loc[:, param_cols] = 0
        weekly_stats[name] = df

    for team_name in weekly_stats:
        np_stats = np.zeros(shape=(len(weekly_stats[team_name]), len(param_cols)))
        for date, df in all_teams_data[team_name].copy().items():
            np_stats += df.loc[:, param_cols].values

        weekly_stats[team_name].loc[:, param_cols] = np_stats
        weekly_stats[team_name].loc[len(weekly_stats[team_name])] = ['Total'] + weekly_stats[team_name][param_cols].sum(axis=0).tolist()
        weekly_stats[team_name].insert(3, 'FG%', weekly_stats[team_name]['FGM'] / weekly_stats[team_name]['FGA'])
        weekly_stats[team_name]['FG%'] = weekly_stats[team_name]['FG%'].apply(lambda x: f"{x:.3f}")

        weekly_stats[team_name].insert(6, 'FT%', weekly_stats[team_name]['FTM'] / weekly_stats[team_name]['FTA'])
        weekly_stats[team_name]['FT%'] = weekly_stats[team_name]['FT%'].apply(lambda x: f"{x:.3f}")
        weekly_stats[team_name].fillna(0, inplace=True)

    with pd.ExcelWriter('output.xlsx') as writer:
        startcol = 0
        for title, df in weekly_stats.items():
            df.to_excel(writer, startcol=startcol, index=False)
            startcol += len(df.columns) + 2
