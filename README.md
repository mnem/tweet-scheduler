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

## Creating a tweet schedule

Sometimes you have a big ol' list of tweets in a file and you want them to be
tweeted at at regular times throughout the year. If that's the case then the
`schedule-lines.py` script will help you.

As it's input, it takes a text file which contains one tweet per line. You then
specify the start date for the tweets, and provide a time pattern for posting
each day. The time pattern is specified as a 24h comma separated list which
goes down to minute granularity.

Using that data, the script reads each line, generates a timestamp, and then outputs
it to a file as a CSV line suitable for importing with the `import-tweets.py`
script above.

Comments can be added to the input file by starting a line with `//` or `#`. To skip a time
slot simply enter an empty line for that slot.

For example, assume we have the following input file:

```
Tweet 1
Tweet 2
// Skip the next time slot

Tweet 3
Tweet 4
Tweet 5
```

We can schedule those tweets to go out twice a day at 9am and 9pm starting from
the first of January 2019 with a line such as:

```bash
pipenv run python schedule-lines.py --start 01/01/2019 --times 0900,2100 --output tweets.csv tweets.txt
```

This reads from `tweets.txt` and outputs to `tweets.csv`, scheduling twice daily
tweets and skipping the morning tweet on the second day (the blank line). It will
output the following CSV file:

```
01/01/2019 09:00,Tweet 1
01/01/2019 21:00,Tweet 2
02/01/2019 21:00,Tweet 3
03/01/2019 09:00,Tweet 4
03/01/2019 21:00,Tweet 5
```

Note that by default data is appended to the output file. If you want to overwrite
the existig content, add the `--overwrite` flag.
