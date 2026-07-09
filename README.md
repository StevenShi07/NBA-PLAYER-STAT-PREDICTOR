# NBA Player Predictor 🏀

A Streamlit web app that estimates NBA player stat hit rates using recent performance, matchup history, and NBA game log data.

## Features

- Search NBA players using a dropdown
- Select opponent team matchup using a dropdown
- Choose Points, Rebounds, or Assists
- Select NBA season
- Choose how many recent games to analyze
- Estimate chance of going over or under a stat line
- Show predicted stat value
- Show confidence level
- Display a recent game trend chart
- Show recent game logs and matchup history tables
- Explain why the prediction was made
- Uses caching and retry logic to reduce NBA API timeout issues

## How It Works

The app pulls NBA player game logs using `nba_api`.

The prediction uses:

- Recent player performance
- Matchup history against the selected opponent
- Historical hit rate over the selected stat line

The app adjusts the weighting based on the number of matchup games available:

- 0 matchup games: 100% recent form
- 1-2 matchup games: 90% recent form / 10% matchup history
- 3+ matchup games: 70% recent form / 30% matchup history

It then calculates:

- Predicted stat value
- Chance of going over the selected line
- Chance of going under the selected line
- Confidence level

## Tech Used

- Python
- Streamlit
- nba_api
- pandas

## Disclaimer

This project is for educational and portfolio purposes only. It is not betting advice.