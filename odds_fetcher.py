import requests
from datetime import datetime, timedelta, timezone
from config import API_KEY, SPORT, REGIONS, MARKETS, ODDS_FORMAT, DATE_FORMAT, SCHEDULE_FILENAME, SCHEDULE_PATH, BUCKET_NAME
import json
from s3_uploader import upload_to_s3, delete_from_s3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class OddsFetcher:
    def __init__(self):
        self.base_url = 'https://api.the-odds-api.com/v4/sports'
    
    def fetch_and_save_homerun_odds(self):
        try: 
            events = self.fetch_events()
            game_ids = [event['id'] for event in events]
            odds_data = {}
            for game_id in game_ids:
                odds_data[game_id] = self.fetch_homerun_odds(game_id)

            self.save_odds(odds_data, SCHEDULE_PATH)

            return odds_data
        except Exception as e:
            logger.error(f"Failed to fetch and save homerun odds: {e}")
            return {}
    
    def save_odds(self, data, file_path):
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file)

    def fetch_events(self):
        today_str, tomorrow_str = self.get_utc_start_and_end()
        try:
            response = requests.get(
                f'{self.base_url}/{SPORT}/events',
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
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            return []

    def fetch_homerun_odds(self, event_id):
        response = requests.get(
            f'{self.base_url}/{SPORT}/events/{event_id}/odds',
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

    def get_utc_start_and_end(self):
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
    

def main(event, lambda_context):
    odds_fetcher = OddsFetcher()
    try:
        logger.info("Deleting old schedule from S3 ...")
        delete_from_s3(BUCKET_NAME, SCHEDULE_FILENAME)
        
        logger.info("Fetching and saving homerun odds ...")
        odds_fetcher.fetch_and_save_homerun_odds()

        logger.info("Uploading new schedule to S3 ...")
        upload_to_s3(SCHEDULE_PATH, BUCKET_NAME, SCHEDULE_FILENAME)

        logger.info("Process complete!")
    except Exception as e:
        logger.error(f"Failed to fetch and save homerun odds: {e}")


if __name__ == '__main__':
    main(event=None, lambda_context=None)