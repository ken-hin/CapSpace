from io import StringIO
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

BASE_URL='https://baseballsavant.mlb.com/leaderboard/statcast-park-factors'
TYPE='year'
YEAR=2026
BAT_SIDE=''
STAT='index_wOBA'
CONDITION='All'
ROLLING=3
PARKS='all'

url = f'{BASE_URL}?type={TYPE}&year={YEAR}&batSide={BAT_SIDE}&stat={STAT}&condition={CONDITION}&rolling={ROLLING}&parks={PARKS}'

# Absolute path to backend/seeds/sports/mlb/park_factors.csv, resolved from this module
OUTPUT = Path(__file__).resolve().parents[3] / "seeds/sports/mlb/park_factors.csv"

def scrape_mlb_park_factor_data(target_url: str = url) -> None:
		# Savant renders the leaderboard table client-side with JavaScript, so the
		# raw HTML has no <table>. Render the page in a headless browser, wait for
		# the table to populate, then hand the rendered HTML to pandas.
		with sync_playwright() as p:
				browser = p.chromium.launch(headless=True)
				page = browser.new_page()
				page.goto(target_url, wait_until="networkidle")
				page.wait_for_selector("table tbody tr")  # rows exist once data loads
				html = page.content()
				browser.close()

		# Reads all tables from the rendered HTML into a list of DataFrames
		dataframes = pd.read_html(StringIO(html))

		# Export the target table to a CSV file
		OUTPUT.parent.mkdir(parents=True, exist_ok=True)
		dataframes[0].to_csv(OUTPUT, index=False)
