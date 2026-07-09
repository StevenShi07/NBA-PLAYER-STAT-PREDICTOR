import streamlit as st
import time
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

st.title("🏀 NBA Player Predictor")
st.caption("Estimate NBA player stat hit rates using recent game logs and matchup history.")

st.info(
    "This app uses recent player form and matchup history to estimate stat hit rates. "
    "This is for educational/project purposes only, not betting advice."
)


# -----------------------------
# Cached NBA API request
# -----------------------------

@st.cache_data(ttl=3600)
def get_player_game_logs(player_id, selected_season):
    """Returns (games, error_message). games is None if all retries failed."""
    last_error = None

    for attempt in range(3):
        try:
            game_log = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=selected_season,
                timeout=90
            )

            games = game_log.get_data_frames()[0]

            # Don't trust the API's default ordering — sort explicitly so
            # "most recent games" is always correct even if that changes.
            games = games.sort_values("GAME_DATE", ascending=False).reset_index(drop=True)

            return games, None

        except Exception as e:
            last_error = str(e)
            time.sleep(3)

    return None, last_error


# -----------------------------
# Get NBA player list
# -----------------------------

all_players = players.get_players()
active_players = [p for p in all_players if p["is_active"]]
player_names = [p["full_name"] for p in active_players]


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
    line = st.number_input("Line", value=20.0, min_value=0.0, step=0.5)

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

    nba_players = players.find_players_by_full_name(player)

    if len(nba_players) == 0:
        st.error("Player not found. Try typing the full name.")

    else:
        player_id = nba_players[0]["id"]

        with st.spinner("Loading NBA stats... this may take a few seconds."):
            games, fetch_error = get_player_game_logs(player_id, selected_season)

        if games is None:
            st.error("NBA.com stats are taking too long to respond. Please try again in a minute.")
            if fetch_error:
                st.caption(f"Details: {fetch_error}")
            st.stop()

        if len(games) == 0:
            st.error("No game logs found for this player in the selected season.")
            st.stop()

        # Games are already sorted most-recent-first by get_player_game_logs.
        # The team abbreviation lives in the MATCHUP string, e.g. "GSW vs. LAL"
        # or "GSW @ LAL" — the first 3 characters are always the player's team
        # for that game.
        current_team = games.iloc[0]["MATCHUP"][:3]

        if opponent == current_team:
            st.error(
                f"{player} currently plays for {opponent_team} ({opponent}) — "
                "pick a different opponent to compare against."
            )
            st.stop()

        if stat == "Points":
            stat_column = "PTS"
        elif stat == "Rebounds":
            stat_column = "REB"
        else:
            stat_column = "AST"

        # Recent form should reflect the player's CURRENT role. If they were
        # traded mid-season, mixing in games from their old team would blend
        # two different usage situations into one "recent average". So recent
        # form only looks at games played with their current team.
        current_team_games = games[games["MATCHUP"].str[:3] == current_team]
        recent_games = current_team_games.head(recent_games_count)

        if len(recent_games) == 0:
            st.error("Not enough recent games with the player's current team to calculate a prediction.")
            st.stop()

        traded_recently = len(recent_games) < recent_games_count and len(current_team_games) < len(games)

        recent_average = recent_games[stat_column].mean()

        recent_games_over_line = recent_games[recent_games[stat_column] > line]
        recent_hit_rate = len(recent_games_over_line) / len(recent_games) * 100

        # Matchup history uses the FULL season (all teams played for), since
        # "how has this player performed against this opponent" is a longer
        # horizon question than "how are they playing right now."
        matchup_games = games[games["MATCHUP"].str.contains(opponent, regex=False)]

        if len(matchup_games) > 0:
            matchup_average = matchup_games[stat_column].mean()

            matchup_games_over_line = matchup_games[matchup_games[stat_column] > line]
            matchup_hit_rate = len(matchup_games_over_line) / len(matchup_games) * 100

            if len(matchup_games) >= 3:
                recent_weight = 0.70
                matchup_weight = 0.30
            else:
                recent_weight = 0.90
                matchup_weight = 0.10

            predicted_value = (recent_average * recent_weight) + (matchup_average * matchup_weight)
            chance_over = (recent_hit_rate * recent_weight) + (matchup_hit_rate * matchup_weight)

        else:
            matchup_average = None
            matchup_hit_rate = None

            recent_weight = 1.00
            matchup_weight = 0.00

            predicted_value = recent_average
            chance_over = recent_hit_rate

        chance_under = 100 - chance_over

        # Confidence: how far the estimate sits from a 50/50 coin flip.
        # >=20 points from 50 (i.e. <=30 or >=70) is High, >=5 points is Medium,
        # otherwise Low. Written this way so the bands are easy to verify.
        distance_from_even = abs(chance_over - 50)

        if distance_from_even >= 20:
            confidence = "High"
        elif distance_from_even >= 5:
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
            st.metric(f"Chance Over {line}", f"{round(chance_over)}%")

        with result_col3:
            st.metric(f"Chance Under {line}", f"{round(chance_under)}%")

        st.write(f"**Confidence:** {confidence}")

        st.write(f"**Player:** {player}")
        st.write(f"**Stat:** {stat}")
        st.write(f"**Line:** {line}")
        st.write(f"**Opponent:** {opponent_team} ({opponent})")
        st.write(f"**Season:** {selected_season}")
        st.write(f"**Recent games used:** {len(recent_games)} (with {current_team})")

        if traded_recently:
            st.warning(
                f"{player} has only played {len(current_team_games)} game(s) with "
                f"{current_team} this season, so the recent-form sample is smaller "
                "than requested. Treat the prediction with extra caution."
            )

        st.subheader("Breakdown")

        st.write(
            f"Recent average: **{round(recent_average, 1)} {stat}** "
            f"(hit rate **{round(recent_hit_rate)}%**) over the last "
            f"**{len(recent_games)} games** with {current_team}."
        )

        if matchup_average is not None:
            st.write(
                f"Average vs {opponent_team} this season: "
                f"**{round(matchup_average, 1)} {stat}** "
                f"(hit rate **{round(matchup_hit_rate)}%**) across "
                f"**{len(matchup_games)} game(s)**."
            )
            st.write(
                f"Final prediction blends **{round(recent_weight * 100)}% recent form** "
                f"with **{round(matchup_weight * 100)}% matchup history**. Matchup weight "
                "is reduced automatically when fewer than 3 games are available, since a "
                "1-2 game sample isn't reliable on its own."
            )
        else:
            st.warning(
                f"No matchup games found vs {opponent_team} this season. "
                "Using recent form only."
            )

        st.subheader(f"Recent {stat} Trend")

        chart_data = recent_games[["GAME_DATE", stat_column]].sort_values("GAME_DATE")
        st.line_chart(chart_data, x="GAME_DATE", y=stat_column)

        st.subheader(f"Last {len(recent_games)} Games ({current_team})")
        st.dataframe(recent_games[["GAME_DATE", "MATCHUP", "PTS", "REB", "AST"]])

        if matchup_average is not None:
            st.subheader(f"Games vs {opponent_team}")
            st.dataframe(matchup_games[["GAME_DATE", "MATCHUP", "PTS", "REB", "AST"]])