# NBA Player Predictor 🏀

A Streamlit web app that estimates NBA player stat hit rates using recent game logs and matchup history.

## Features

- Search NBA players using a dropdown
- Select opponent team matchup
- Choose Points, Rebounds, or Assists
- Select NBA season
- Choose how many recent games to analyze
- Estimate chance of going over or under a stat line
- Show confidence level
- Display recent game trend chart
- Show recent games and matchup history tables

## How It Works

The app uses NBA player game logs from `nba_api`.

The prediction combines:

- 70% recent player form
- 30% matchup history against the selected opponent

It also calculates how often the player went over the selected stat line.

## Tech Used

- Python
- Streamlit
- nba_api
- pandas

## Disclaimer

This project is for educational and portfolio purposes only. It is not betting advice.