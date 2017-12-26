from datetime import datetime
import sqlite3
import pytz

class TweetStore(object):
    """Interface to schedule tweet storage. General use is:

            with TweetStore() as ts:
                # use ts object

        Using it this way ensure data is saved to the underlying storage."""

    def __init__(self, storage_name="scheduled-tweets.db"):
        self._storage_name = storage_name

    ########################################################################
    # Properties
    @property
    def storage_name(self):
        return self._storage_name

    ########################################################################
    # Data writing
    def schedule_tweet(self, date, text, url=None):
        # Convert the date to UTC and remove the timezone. This
        # allows us to use SQL functions to compare dates
        date = date.astimezone(pytz.utc).replace(tzinfo=None)

        if url is not None and len(url) > 0:
            if not url.lower().startswith('http'):
                url = "http://{}".format(url)
            self._cursor.execute('''INSERT INTO tweets (tweet_on_date, tweet_text, tweet_url) VALUES (?,?,?)''', (date, text, url))
        else:
            self._cursor.execute('''INSERT INTO tweets (tweet_on_date, tweet_text) VALUES (?,?)''', (date, text))

    ########################################################################
    # Data reading
    def process_due_tweets(self, processor):
        """Allows the processing of all scheduled tweets which have not already
           been successfully processed. They are processed by the supplied
           processing function.

           The processing function should have the signature:

                processor(tweet, scheduled_date)

           If the tweet is successfully processed it should return the string
           ID of the posted tweet, otherwise return None."""
        self._cursor.execute('''SELECT * FROM tweets 
                                    WHERE tweeted_date IS NULL AND DATETIME(tweet_on_date) <= DATETIME('now')
                                    ORDER BY tweet_on_date ASC''')
        due_rows = self._cursor.fetchall()
        for row in due_rows:
            row_id = row['schedule_id']
            row_tweet = row['tweet_text']
            row_scheduled_date = row['tweet_on_date']
            row_url = row['tweet_url']

            full_tweet = row_tweet
            if row_url is not None:
                full_tweet = "{} {}".format(row_tweet, row_url)

            tweet_id = processor(full_tweet, row_scheduled_date)
            if tweet_id is not None and len(tweet_id) > 0:
                self._cursor.execute('''UPDATE tweets SET tweeted_date=?, tweet_id=? WHERE schedule_id=?''', (datetime.now(), tweet_id, row_id))

    ########################################################################
    # General usage
    def __enter__(self):
        self.__create_connection()
        self.__ensure_table()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._connection is not None:
            try:
                self._connection.commit()
            except Exception as e:
                raise e
            finally:
                self.__destroy_connection()


    ########################################################################
    # Private database related methods
    def __create_connection(self):
        self._connection = sqlite3.connect(self.storage_name)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()

    def __destroy_connection(self):
        self._connection.close()
        self._cursor = None
        self._connection = None

    def __ensure_table(self):
        self._cursor.execute('''CREATE TABLE IF NOT EXISTS tweets (
                                    schedule_id INTEGER PRIMARY KEY,
                                    tweet_on_date TIMESTAMP NOT NULL,
                                    tweet_id TEXT default NULL, 
                                    tweeted_date TIMESTAMP default NULL,
                                    tweet_text TEXT NOT NULL, 
                                    tweet_url TEXT default NULL)''')

    def __str__(self):
        return "<TweetStore: storage_name='{}'>".format(self.storage_name)
