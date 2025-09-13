import requests
import pandas as pd
import sqlite3
import time
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
from .path_management import data_dir

class CachedAPIClient:
    """
    Generic API client that caches responses to avoid repeated requests.
    """

    def __init__(self, cache_name: str = "api_cache", 
                cache_dir: Path = None, cache_hours: int = 24):
        """
        Initialize API client with caching capabilities.
        
        Args:
            cache_name: Name for this cache (allows multiple separate caches)
            cache_dir: Directory to store cache files (default: data/cache)
            cache_hours: How many hours to keep cached data fresh
        """
        self.cache_dir = cache_dir or (data_dir / "cache")
        self.cache_hours = cache_hours

        # Setup logging so you can see what's happening
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(f"{__name__}.{cache_name}")

        # Create separate cache database for this dataset
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / f"{cache_name}.db"
        self._init_cache_db()

        # Rate limiting: prevents overwhelming the API server
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Wait 100ms between requests

    def _init_cache_db(self):
        """
        Create SQLite database to store API responses.
        This lets us avoid making the same API call twice.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS api_responses (
                cache_key TEXT PRIMARY KEY,
                url TEXT,
                response_data TEXT,
                timestamp DATETIME
            )
        ''')
        conn.commit()
        conn.close()
        self.logger.info(f"Cache database ready: {self.db_path}")

    def _generate_cache_key(self, url: str) -> str:
        """
        Create unique identifier for each URL.
        Same URL = same cache key.
        """
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """
        Check if we already have fresh data for this URL.
        Returns cached data if it's newer than cache_hours, otherwise None.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Only use cache if it's fresh (within our time limit)
        cutoff_time = datetime.now() - timedelta(hours=self.cache_hours)
        cursor.execute('''
            SELECT response_data FROM api_responses 
            WHERE cache_key = ? AND timestamp > ?
        ''', (cache_key, cutoff_time))

        result = cursor.fetchone()
        conn.close()

        if result:
            self.logger.info("Found fresh cached data - using cache instead of API")
            return json.loads(result[0])
        return None

    def _cache_response(self, cache_key: str, url: str, response_data: Dict):
        """
        Save API response to cache so we don't need to fetch it again.
        Stores the response data along with when we got it.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT OR REPLACE INTO api_responses 
            (cache_key, url, response_data, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (cache_key, url, json.dumps(response_data), datetime.now()))
        conn.commit()
        conn.close()
        self.logger.info("API response saved to cache")

    def _rate_limit(self):
        """
        Enforce minimum time between API requests.
        Prevents hitting rate limits that could get you temporarily blocked.
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_request(self, url: str) -> requests.Response:
        """
        Make HTTP request to API with rate limiting.
        Waits between requests and handles basic error checking.
        """
        self._rate_limit()  # Wait if we're calling too fast

        self.logger.info(f"Making API request to: {url}")
        response = requests.get(url)

        # Check if the API call was successful
        if response.status_code != 200:
            error_msg = f"API request failed with status {response.status_code}: {response.text}"
            self.logger.error(error_msg)
            raise requests.RequestException(error_msg)

        self.logger.info("API request completed successfully")
        return response

    def get_data(self, url: str) -> pd.DataFrame:
        """
        Fetch data from API endpoint with automatic caching.
        
        This is the main method you'll use. Give it a complete URL
        and it will either return cached data or make a fresh API call.
        
        Args:
            url: Complete API URL with all parameters included
        
        Returns:
            pandas DataFrame with the API response data
        """

        # Check if we have this data cached already
        cache_key = self._generate_cache_key(url)
        cached_data = self._get_cached_response(cache_key)

        if cached_data:
            data = cached_data
        else:
            # Make fresh API request
            response = self._make_request(url)
            data = response.json()

            # Save response to cache for next time
            self._cache_response(cache_key, url, data)

        # Convert API response to pandas DataFrame
        return self._clean_dataframe(data)

    def _clean_dataframe(self, data) -> pd.DataFrame:
        """
        Convert API JSON response to pandas DataFrame.
        
        Most APIs return data as [column_names, row1, row2, ...].
        This converts that format into a proper DataFrame.
        """
        if not data or len(data) < 2:
            raise ValueError("API returned empty or invalid data")

        # First row is column names, rest are data rows
        df = pd.DataFrame(data[1:], columns=data[0])

        self.logger.info(f"Created DataFrame: {len(df)} rows × {len(df.columns)} columns")
        return df

    def clear_old_cache(self, days_old: int = 30) -> int:
        """
        Remove cached responses older than specified days.
        
        Useful for cleaning up disk space and ensuring you don't accidentally
        use very old data. Returns number of items deleted.
        """
        conn = sqlite3.connect(self.db_path)
        cutoff_date = datetime.now() - timedelta(days=days_old)

        cursor = conn.cursor()
        cursor.execute('DELETE FROM api_responses WHERE timestamp < ?',(cutoff_date,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        self.logger.info(f"Deleted {deleted_count} old cache entries")
        return deleted_count

    def get_cache_info(self) -> Dict:
        """
        Get statistics about what's in the cache.
        
        Useful for understanding how much data you have cached
        and whether you need to clean up old entries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count total cached responses
        cursor.execute('SELECT COUNT(*) FROM api_responses')
        total_items = cursor.fetchone()[0]

        # Count fresh responses (within cache_hours)
        cutoff_time = datetime.now() - timedelta(hours=self.cache_hours)
        cursor.execute('SELECT COUNT(*) FROM api_responses WHERE timestamp> ?', (cutoff_time,))
        fresh_items = cursor.fetchone()[0]

        conn.close()

        return {
            'total_cached_responses': total_items,
            'fresh_responses': fresh_items,
            'stale_responses': total_items - fresh_items,
            'cache_file': str(self.db_path)
        }