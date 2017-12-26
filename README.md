# tweet-scheduler

Simplistic system for scheduling tweets. Allows bulk import from CSV files
and keeps track of which tweets have been posted.

## Prerequisites

It's highly recommended that you use pipenv to run the scripts here to ensure
the correct Python 3 environment:

1. Install pipenv
2. Install the project dependencies with `pipenv install`

## Importing scheduled tweets

Tweets may be imported from a CSV file of the format:

    <tweet date>,<tweet text>,<optional URL>

Dates are in UK format: `day/month/year 24h:minutes`. For example `01/01/2018 18:30`
means post the tweet on or after January 1st 2018 at 6.30pm. If no timezone information
is specified, the time is assumed to be in the timezone `Europe/London`. The default
timezone for timezoneless entries may be specified by passing `--timezone 'Europe/London'`
to the import script.

Here's an example of importing tweets to the default `scheduled-tweets.db`:

    pipenv run python import-tweets.py csv my-scheduled-tweets.csv

This will append, or create and add, scheduled tweets into the sqlite database
called `scheduled-tweets.db`.

## Posting scheduled tweets

To post scheduled tweets to your account, you must create an twitter application
in your account in order to fetch the authentication credentials from it. To 
create the application see https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens

Once you have the application created, you will need the several tokens from it.
Create a file to store these values (make sure that it isn't world readable and
*definitely* do not check them in to source control...) and store them in a 
single line in the format:

    consumer_key consumer_secret access_token_key access_token_secret

The tokens can be found by going to the application you created and navigating
to the "Keys and Access Tokens" tab.

Once you have the file with the credentials, you can post scheduled tweets
by calling the `post-scheduled-tweets.py` script. For example:

    pipenv run python post-scheduled-tweets.py --credentials my_creds_file scheduled-tweets.db

This well fetch any tweets due to be posted from the database, post them, and then
record their ID and time of posting in the database. It's safe to run the script
again - tweets with a sending date won't be reposted.

Generally, you will want to call this script at regular intervals. The simplest
way to do that is to add an entry in your crontab. You can generate a string
which calls the script every 5 minutes by running:

    pipenv run python post-scheduled-tweets.py --showcron --credentials my_creds_file scheduled-tweets.db

Copy the output string and add it to your crontab (e.g. `crontab -e` and paste).
