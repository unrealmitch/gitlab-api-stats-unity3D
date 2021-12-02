# Gitlab Statistics 4 Unity

Simple script to get statistics from Gitlab and collect them in a csv.

Get all commits data (with diff stats), with different filters of files (gitlab_statistics.py).

The resulting csv can be used in excel, google sheets or PowerBI,  in order to obtain reports from projects and authors with pivot/dynamic tables.

The default statistics are oriented for Unity projects.

Also can automatic upload the csv to a google sheets, configure in gsheets.py

Config different parammeters in gitlab_config

CMD Args: [0] Start date to get commits (yyyy-mm-dd) ex: python gitlab.py 2018-01-01
          [0] all -> get all commits of all times, ex: python gitlab.py all

## Info
Author: unrealmitch@gmail.com

Python version: 3.9

Gitlab API: v4
