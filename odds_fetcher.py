import requests
from datetime import datetime, timedelta, timezone
from .config import API_KEY, SPORT, REGIONS, MARKETS, ODDS_FORMAT, DATE_FORMAT
import json
from s3_uploader import upload_to_s3, delete_from_s3, get_object, download_object

BUCKET_NAME = 'timjimmymlbdata'
JSON_FILE = 'mlb_schedule.json'
JSON_FILE_PATH = '/tmp/mlb_schedule.json'

class OddsFetcher:
    def fetch_and_save_homerun_odds():
        """
        Fetches homerun odds from the API for a list of game IDs and saves it to a JSON file.

        Args:
            game_ids (list): The list of game IDs to fetch the odds for.

        Returns:
            dict: The combined odds data fetched from the API.
        """
        # Get all the events for today
        # TODO: Can call fetch events once per day and store the data in a file
        events = OddsFetcher.fetch_events()
        game_ids = [event['id'] for event in events]

        # Load existing data if available
        if get_object(BUCKET_NAME, JSON_FILE) == False:
            existing_data = {'entries': []}
        else:
            download_object(BUCKET_NAME, JSON_FILE, JSON_FILE_PATH)
            with open(JSON_FILE_PATH, 'r') as json_file:
                existing_data = json.load(json_file)

        combined_odds_data = {}
        for game_id in game_ids:
            odds_data = OddsFetcher.fetch_homerun_odds(game_id)
            combined_odds_data[game_id] = odds_data

        # Add new entry with timestamp
        new_entry = {
            'timestamp': datetime.now().isoformat(),
            'data': combined_odds_data
        }
        existing_data['entries'].append(new_entry)

        # Upload the updated data to S3
        upload_to_s3(BUCKET_NAME, JSON_FILE, JSON_FILE_PATH)

        return combined_odds_data

    def fetch_events():
        """
        Fetch today's MLB events using the Odds API.
        """
        today_str, tomorrow_str = OddsFetcher.get_utc_start_and_end()

        response = requests.get(
            f'https://api.the-odds-api.com/v4/sports/{SPORT}/events',
            params={
                'apiKey' : API_KEY,
                'commenceTimeFrom': today_str,
                'commenceTimeTo': tomorrow_str,
                'dateFormat': 'iso'
            }
        )

        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch odds: {response.status_code}, {response.text}")

        return response.json()

    def fetch_homerun_odds(event_id):
        response = requests.get(
            f'https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds',
            params={
                'apiKey' : API_KEY,
                'regions' : REGIONS,
                'markets' : MARKETS,
                'oddsFormat' : ODDS_FORMAT,
                'dateFormat' : DATE_FORMAT
            }
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch odds: {response.status_code}, {response.text}")

        return response.json()


    def get_utc_start_and_end():
        """
        Get the start and end times for today in UTC.

        Returns:
            tuple: A tuple containing the start and end times in ISO 8601 format.
        """
        # Get the current UTC time
        now_utc = datetime.now(timezone.utc)

        # Reset the time to midnight of the start day
        now_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Set the end time to 2 AM of the next day
        end_of_today_utc = now_utc + timedelta(days=1, hours=2)

        # Convert the times to ISO 8601 format
        today_str = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end_of_today_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

        return today_str, end_str