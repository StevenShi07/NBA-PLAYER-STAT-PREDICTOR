import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

st.title("🏀 NBA Player Predictor")
st.caption("Estimate NBA player stat hit rates using recent game logs and matchup history.")

st.info(
    "This app uses recent player form and matchup history to estimate stat hit rates. "
    "This is for educational/project purposes only, not betting advice."
)

# -----------------------------
# Get NBA player list
# -----------------------------

all_players = players.get_players()

active_players = []

for p in all_players:
    if p["is_active"] == True:
        active_players.append(p)

player_names = []

for p in active_players:
    player_names.append(p["full_name"])


# -----------------------------
# NBA team list
# -----------------------------

teams = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "LA Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS"
}


# -----------------------------
# User inputs
# -----------------------------

col1, col2 = st.columns(2)

with col1:
    player = st.selectbox("Player Name", player_names)

with col2:
    opponent_team = st.selectbox("Opponent Team", list(teams.keys()))

col3, col4, col5 = st.columns(3)

with col3:
    stat = st.selectbox(
        "Stat",
        ["Points", "Rebounds", "Assists"]
    )

with col4:
    line = st.number_input("Line", value=30)

with col5:
    selected_season = st.selectbox(
        "Season",
        ["2024-25", "2023-24", "2022-23"]
    )

recent_games_count = st.selectbox(
    "Recent Games Used",
    [5, 10, 15, 20],
    index=1
)

opponent = teams[opponent_team]


# -----------------------------
# Prediction button
# -----------------------------

if st.button("Predict"):

    if player == "":
        st.warning("Please enter a player name.")

    else:
        nba_players = players.find_players_by_full_name(player)

        if len(nba_players) == 0:
            st.error("Player not found. Try typing the full name.")

        else:
            player_id = nba_players[0]["id"]

            game_log = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=selected_season
            )

            games = game_log.get_data_frames()[0]

            if len(games) == 0:
                st.error("No game logs found for this player in the selected season.")
                st.stop()

            if stat == "Points":
                stat_column = "PTS"
            elif stat == "Rebounds":
                stat_column = "REB"
            else:
                stat_column = "AST"

            recent_games = games.head(recent_games_count)

            if len(recent_games) == 0:
                st.error("Not enough recent games to calculate a prediction.")
                st.stop()

            recent_average = recent_games[stat_column].mean()

            recent_games_over_line = recent_games[
                recent_games[stat_column] > line
            ]

            recent_hit_rate = len(recent_games_over_line) / len(recent_games) * 100

            matchup_games = games[games["MATCHUP"].str.contains(opponent)]

            if len(matchup_games) > 0:
                matchup_average = matchup_games[stat_column].mean()

                matchup_games_over_line = matchup_games[
                    matchup_games[stat_column] > line
                ]

                matchup_hit_rate = len(matchup_games_over_line) / len(matchup_games) * 100

                if len(matchup_games) >= 3:
                    recent_weight = 0.70
                    matchup_weight = 0.30

                else:
                    recent_weight = 0.90
                    matchup_weight = 0.10

                predicted_value = (recent_average * recent_weight) + (
                    matchup_average * matchup_weight
                )

                chance_over = (recent_hit_rate * recent_weight) + (
                    matchup_hit_rate * matchup_weight
                )

            else:
                matchup_average = None
                matchup_hit_rate = None

                recent_weight = 1.00
                matchup_weight = 0.00

                predicted_value = recent_average

                chance_over = recent_hit_rate

            # Calculate chance under
            chance_under = 100 - chance_over

            # Confidence label
            if chance_over >= 70 or chance_over <= 30:
                confidence = "High"
            elif chance_over >= 55 or chance_over <= 45:
                confidence = "Medium"
            else:
                confidence = "Low"


            # -----------------------------
            # Results
            # -----------------------------

            st.subheader("Prediction Result")

            result_col1, result_col2, result_col3 = st.columns(3)

            with result_col1:
                st.metric(f"Predicted {stat}", round(predicted_value, 1))

            with result_col2:
                st.metric(
                    f"Chance Over {line}",
                    f"{round(chance_over)}%"
                )

            with result_col3:
                st.metric(
                    f"Chance Under {line}",
                    f"{round(chance_under)}%"
                )

            st.write(f"**Confidence:** {confidence}")

            st.write(f"**Player:** {player}")
            st.write(f"**Stat:** {stat}")
            st.write(f"**Line:** {line}")
            st.write(f"**Opponent:** {opponent_team} ({opponent})")
            st.write(f"**Season:** {selected_season}")
            st.write(f"**Recent games used:** {recent_games_count}")

            st.subheader("Breakdown")

            st.write(f"Recent average: **{round(recent_average, 1)} {stat}**")
            st.write(f"Recent hit rate: **{round(recent_hit_rate)}%**")

            if matchup_average is not None:
                st.write(
                    f"Average vs {opponent_team}: "
                    f"**{round(matchup_average, 1)} {stat}**"
                )

                st.write(
                    f"Hit rate vs {opponent_team}: "
                    f"**{round(matchup_hit_rate)}%**"
                )

                st.write(
                    f"Final prediction uses **{round(recent_weight * 100)}% recent form** "
                    f"and **{round(matchup_weight * 100)}% matchup history**."
                )

            else:
                st.warning(
                    f"No matchup games found vs {opponent_team}. "
                    "Using recent games only."
                )

            st.subheader("Why this prediction?")

            st.write(
                f"{player} has averaged **{round(recent_average, 1)} {stat}** "
                f"over the last **{recent_games_count} games**."
            )

            if matchup_average is not None:
                st.write(
                    f"Against the **{opponent_team}**, {player} has averaged "
                    f"**{round(matchup_average, 1)} {stat}** this season."
                )

                st.write(
                    f"The final prediction weighs **{round(recent_weight * 100)}% recent form** "
                    f"and **{round(matchup_weight * 100)}% matchup history**."
                )

            else:
                st.write(
                    f"No matchup history was found against the **{opponent_team}**, "
                    "so the prediction only uses recent form."
                )

            st.write(
                f"The app estimates a **{round(chance_over)}%** chance of going over "
                f"and a **{round(chance_under)}%** chance of going under."
            )

            st.subheader(f"Recent {stat} Trend")

            chart_data = recent_games[["GAME_DATE", stat_column]].copy()

            chart_data = chart_data.sort_values("GAME_DATE")

            st.line_chart(
                chart_data,
                x="GAME_DATE",
                y=stat_column
            )

            st.subheader(f"Last {recent_games_count} Games")

            st.dataframe(
                recent_games[["GAME_DATE", "MATCHUP", "PTS", "REB", "AST"]]
            )

            if matchup_average is not None:
                st.subheader(f"Games vs {opponent_team}")

                st.dataframe(
                    matchup_games[["GAME_DATE", "MATCHUP", "PTS", "REB", "AST"]]
                )