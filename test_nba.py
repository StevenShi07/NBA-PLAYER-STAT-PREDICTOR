from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

player_name = "Stephen Curry"

nba_players = players.find_players_by_full_name(player_name)

print(nba_players)

player_id = nba_players[0]["id"]

game_log = playergamelog.PlayerGameLog(player_id=player_id, season="2023-24")

games = game_log.get_data_frames()[0]

print(games[["GAME_DATE", "MATCHUP", "PTS", "REB", "AST"]].head(10))