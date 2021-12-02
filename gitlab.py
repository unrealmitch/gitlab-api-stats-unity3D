# -*- coding: utf-8 -*-
# Simple script to get statistics from Gitlab and collect them in a csv.
# Get all commits data (with diff stats), with different filters of files (gitlab_statistics.py).
# The resulting csv can be used in excel, google sheets or PowerBI, 
# in order to obtain reports from projects and authors with pivot/dynamic tables.
# The default statistics are oriented for Unity projects.
# Config diferent parammeters in gitlab_config
# CMD Args: [0] Start date to get commits (yyyy-mm-dd) ex: python gitlab.py 2018-01-01
# CMD Args: [0] all -> get all commits of all times, ex: python gitlab.py all

# Author: unrealmitch@gmail.com
# Python version: 3.9
# Gitlab API: v4

# Dependencies (to use google sheet upload):
# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

import requests
import json
import os
import sys
import importlib
import time
from datetime import datetime, timedelta
import re
importlib.reload(sys)
from gitlab_config import *
from gitlab_statistics import *
from gsheets import *

importlib.reload(sys)

now = datetime.now()
now_date = now.strftime("%Y-%m-%d")
now_time = now.strftime("%Y-%m-%d--%H-%M-%S")
savePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), now_time)

page = 1
projects = json.loads("{}")
project_stats = json.loads("{}")
workers = json.loads("{}")
workers_stats = json.loads("{}")

fetchAll = False

def ReplaceAuthors(text):
    for (aorig, adest) in replaces:
        text = text.replace(aorig,adest)
    return text

def Save(name, string):
    if(not os.path.exists(savePath)):
        os.makedirs(savePath)
    path = os.path.join(savePath,name)
    text_file = open(path, "w", encoding='utf-8')
    text_file.write(string)
    text_file.close()

def SaveData():
    csv = "id;name;group;worker;commits;stats;add;filteredadd\n"
    csv2 = "id;name;group;cid;ctitle;cauthor;cdate;cadd;cdel;cstat;cfil;url\n"

    for project_id, project_v in project_stats.items():
        for worker_id, worker in project_v["workers"].items():
            csv += str(project_id) + ";" + project_v["name"] + ";" + project_v["group"] + ";" + worker_id + ";" + str(worker["c"]) + ";" + str(worker["s"]) + ";" + str(worker["a"]) + ";" + str(worker["fa"]) + "\n"

        for commit_id, cvalue in project_v["commits"].items():
            csv2 += str(project_id) + ";" + project_v["name"] + ";" + project_v["group"] + ";" + str(commit_id) + ";'" + cvalue["t"].replace(";",",.") + "';" + str(cvalue["a"]) + ";" + str(cvalue["d"]) + ";" + str(cvalue["sa"]) + ";" + str(cvalue["sd"]) + ";" + str(cvalue["st"]) + ";" + str(cvalue["sf"]) + ";" + cvalue["url"] + "\n"

    Save("Projects.csv", ReplaceAuthors(csv))
    Save("Commits.csv", ReplaceAuthors(csv2))

    csv3 = "worker;commits;stats;add;filteredadd\n"
    for worker_id, worker in workers_stats.items():
        csv3 += worker_id + ";" + str(worker["c"]) + ";" + str(worker["s"]) + ";" + str(worker["a"]) + ";" + str(worker["fa"]) + "\n"
    Save("Workers.csv", ReplaceAuthors(csv3))

    if(include_more_stats):
        csv4 = "id;name;group;cid;ctitle;cauthor;cdate;cadd;cdel;cstat;cfil;url;c1"
        dicGroups = GetMoreStateDic()
        # Files Changed, Total Changes (@@ .. @@), Total Adds, Total Deletes, Total Add Lines, Total Delete Lines
        for fileGroup  in dicGroups:
            csv4 += ";" + fileGroup + "-fc;" + fileGroup + "-tc;" + fileGroup + "-ta;" + fileGroup + "-td;" + fileGroup + "-la;" + fileGroup + "-ld"
        csv4 += "\n"
        for project_id, project_v in project_stats.items():
            for commit_id, cvalue in project_v["commits"].items():
                csv4 += str(project_id) + ";" + project_v["name"] + ";" + project_v["group"] + ";" + str(commit_id) + ";'" + cvalue["t"].replace(";",",.") + "';" + str(cvalue["a"]) + ";" + str(cvalue["d"]) + ";" + str(cvalue["sa"]) + ";" + str(cvalue["sd"]) + ";" + str(cvalue["st"]) + ";" + str(cvalue["sf"]) + ";" + cvalue["url"]
                csv4 += ";" +  str(cvalue["c1"]) if "c1" in cvalue else "0"
                for fileGroup in dicGroups:
                    if("stats" in cvalue):
                        statsg = cvalue["stats"][fileGroup]
                    else:
                        statsg = (0,0,0,0,0,0)
                    csv4 += ";" + str(statsg[0]) + ";" + str(statsg[1]) + ";" + str(statsg[2]) + ";" + str(statsg[3]) + ";" + str(statsg[4]) + ";" + str(statsg[5])
                csv4 += "\n"

        Save("CommitsStats.csv", ReplaceAuthors(csv4))

def SaveRawData():
    pathJ = os.path.join(savePath,"dump-project.json")
    with open(pathJ, 'w') as outfile:
        json.dump(projects, outfile, indent=2)

    pathJ = os.path.join(savePath , "dump-commits.json")
    with open(pathJ, 'w') as outfile:
        json.dump(project_stats, outfile, indent=2)

def UploadToGoogleSheets():
    replace = fetchAll

    dicGroups = GetMoreStateDic()
    gCommits = []
    jiraRE = r"[a-zA-Z0-9]+-[0-9]+ "
    for project_id, project_v in project_stats.items():
        for commit_id, cvalue in project_v["commits"].items():
            cTitle = cvalue["t"]
            title = '="' + cTitle.replace(";",",.").replace('"', "'") + '"'
            id = '="' + str(commit_id) + '"'
            cDate = '="' + str(cvalue["d"]) + '"'
            cDateParsed = str(cvalue["d"]).split(".")[0].replace("T", " ")
            cAuthor = ReplaceAuthors(str(cvalue["a"]))
            cJiraIssue = ""
            searchJira = re.findall(jiraRE, cTitle, re.IGNORECASE)
            if(searchJira):
                # cJiraIssue = searchJira.group()
                for match in searchJira:
                    cJiraIssue = cJiraIssue + str(match) + " "
                cJiraIssue = cJiraIssue.strip()

            isMerge = cTitle.startswith("Merge") if "1" else "0" 
            
            values = [str(project_id), project_v["name"], project_v["group"], id, title, 
                    cAuthor, cDateParsed, cDate, cJiraIssue, 
                    str(cvalue["sa"]), str(cvalue["sd"]), str(cvalue["st"]), str(cvalue["sf"]), cvalue["url"],
                    isMerge]

            if(fetchAll):
                values.append( str(cvalue["c1"]) if "c1" in cvalue else "0" )
            else:
                values.append( 0 )
            
            for fileGroup in dicGroups:
                if("stats" in cvalue):
                    statsg = cvalue["stats"][fileGroup]
                else:
                    statsg = (0,0,0,0,0,0)

                for stat in statsg:
                    values.extend( [str(stat)] )
            
            gCommits.append(values)
    
    if(replace):
        print("# Replace commits in Google sheets... ", len(gCommits))
        replaceCommitsGoogleSheet(gCommits)
    else:
        print("# Append commits to Google sheets... ", len(gCommits))
        appendCommitsGoogleSheet(gCommits)

    print("# Upload Google Sheet completed!")

print("# Starting... " , now_time)
print("# Getting projects info...")
print("")

while True:
    url = git_url + "/api/v4/projects"
    payload={'simple': 'true','per_page': '1000','page': page}
    files=[]
    headers = {'PRIVATE-TOKEN': git_token}

    response = requests.request("GET", url, headers=headers, data=payload, files=files)
    #print(response.text)

    if response.text == '[]':
        break

    jsonProjects = json.loads(response.text)

    if page != 1:
        projects = projects + jsonProjects
    else:
        projects = jsonProjects

    page += 1

projects.reverse()
#projects_full = projects.copy()

print("Projects [" + str(len(projects)) + "]")

until = ""

if len(sys.argv) > 1:
    if(sys.argv[1] == "all"):
        fetchAll = True
        since = "2010-01-01T00:00:00Z"
    else:
        since = sys.argv[1] + "T00:00:00Z"
elif(default_start_yesterday):
    yesterday = now - timedelta(days=1)
    since = yesterday.strftime("%Y-%m-%d") + "T00:00:00Z"
    if(default_stop_yesterday_midnight):
        until = now_date + "T00:00:00Z"
elif(default_start and len(default_start) == 10):
    since = default_start + "T00:00:00Z"
else:
    since = ""

if(until != "" ):
    print("Getting commits since: " + since + " -> " + until)
else:
    print("Getting commits since: " + since + " -> " + now_time)
    

iProject = 0
tProject = 0
iCommit = 0
for project in projects:
    iProject += 1
    tProject += 1
    id = project["id"]

    if(id < min_proj or id in ommitProjects): continue

    name = project["name"]
    print("")
    print ("[" + str(id) + "] " + name + "  (" + str(tProject) + "/" + str(len(projects)) + ")"),

    url = git_url + "/api/v4/projects/" + str(id) + "/repository/commits"
    files=[]
    headers = {'PRIVATE-TOKEN': git_token}

    jsonCommits = []
    pageCommit = 1
    error = 1

    while True: 
        payload={'per_page': commitsPerPage, 'page': pageCommit, 
        'with_stats': include_stats and error < maxErrors if 'true' else 'false',
        'since' : since}

        if(until != ""):
            payload["until"] = until

        tries = 0
        while(tries <= 3):
            tries += 1
            try:
                response = requests.request("GET", url, headers=headers, data=payload, files=files)
                if(response.status_code == 200):
                    break
                else:
                    sys.stdout.write("_")
                    time.sleep(5)
            except:
                sys.stdout.write("_")
                time.sleep(5)
        
        if response.status_code == 200:
            jsonCommits = jsonCommits + json.loads(response.text)
            if response.text == '[]': break
            else: sys.stdout.write("." if include_stats and error < maxErrors else "_")

            error = 0
            pageCommit +=1
        else:
            print("E(" + str(pageCommit) + "):" + str(response.status_code) ),
            if error >= maxErrors + 1:
                print("!S(" + str(pageCommit) + ")!"),
                error = 0
                pageCommit +=1
            else:
                error += 1
   
    if(reverse_commits_older):
        jsonCommits = list(reversed(jsonCommits))
    print(str(len(jsonCommits)) + " commits")
    project["commits"] = jsonCommits
    project_stats[id] = {"name" : name, "group" : project["namespace"]["name"] , "workers":{}, "commits":{}}

    for commit in jsonCommits:
        iCommit += 1
        autor = str(commit["author_email"])

        if autor in workers:
            workers[autor] = workers[autor]+1 
        else:
            workers[autor] = 1

        haveStats = include_stats and "stats" in commit

        stats = commit["stats"]["total"] if haveStats else 0
        add = commit["stats"]["additions"] if haveStats else 0
        deletions = commit["stats"]["deletions"] if haveStats else 0
        fadd = max_add_per_commit if add > max_add_per_commit else add

        if autor in workers_stats:
            workers_stats[autor]["c"] = workers_stats[autor]["c"]+1
            workers_stats[autor]["s"] = workers_stats[autor]["s"]+stats
            workers_stats[autor]["a"] = workers_stats[autor]["a"]+add
            workers_stats[autor]["fa"] = workers_stats[autor]["fa"]+fadd
        else:
            workers_stats[autor] = {"c" : 1, "s" : stats, "a" : add, "fa" : fadd}

        if autor in project_stats[id]["workers"]:
            project_stats[id]["workers"][autor]["c"] = project_stats[id]["workers"][autor]["c"]+1
            project_stats[id]["workers"][autor]["s"] = project_stats[id]["workers"][autor]["s"]+stats
            project_stats[id]["workers"][autor]["a"] = project_stats[id]["workers"][autor]["a"]+add
            project_stats[id]["workers"][autor]["fa"] = project_stats[id]["workers"][autor]["fa"]+fadd
        else:
            project_stats[id]["workers"][autor] = {"c" : 1, "s" : stats, "a" : add, "fa" : fadd}

        project_stats[id]["commits"][commit["short_id"]] = {
            "t": commit["title"], "a":autor, "d": commit["created_at"], "sa": add, "sd": deletions, "st" : stats, "sf" : fadd, "url" : commit["web_url"]
        }

        if(reverse_commits_older):
            project_stats[id]["commits"][commit["short_id"]]["c1"] = 1 if commit == jsonCommits[0] else 0
        else:
            project_stats[id]["commits"][commit["short_id"]]["c1"] = 1 if commit == jsonCommits[-1] else 0

        if(include_more_stats):
            project_stats[id]["commits"][commit["short_id"]]["stats"] = { }
            resultStates = GetMoreStateDic()
            for key in resultStates:
                project_stats[id]["commits"][commit["short_id"]]["stats"][key] = resultStates[key]
            
            project_stats[id]["commits"][commit["short_id"]]["stats"]["files"] = {}

            if debugmode:
                print("\n## Commit: " + str(commit["id"])) 

            urlCommit = git_url + "/api/v4/projects/" + str(id) + "/repository/commits/" + str(commit["id"]) + "/diff"
            triesInfo = 0
            while(triesInfo <= 3):
                triesInfo += 1
                try:
                    responseC = requests.request("GET", urlCommit, headers=headers, data=[], files=[])
                    if(responseC.status_code == 200):
                        break
                    else:
                        sys.stdout.write("!")
                        time.sleep(5)
                except:
                    sys.stdout.write("!")
                    time.sleep(5)

            if responseC.status_code == 200:
                sys.stdout.write("+")
                commitDiff = json.loads(responseC.text)
                
                for difs in commitDiff:
                    diffText = difs["diff"]
                    if("@@" in diffText):
                        stats = GetMoreStatsDiff(diffText)
                    else:
                        new = 1 if difs["new_file"] == "true" else 0
                        deleted = 1 if difs["deleted_file"] == "true" else 0
                        stats = (1, new, deleted, new, deleted)

                    path = difs["new_path"]
                    extensionGroup = GetStatsFileGroup(path)
                    resultStates[extensionGroup][0] += 1
                    resultStates[extensionGroup][1] += stats[0]
                    resultStates[extensionGroup][2] += stats[1]
                    resultStates[extensionGroup][3] += stats[2]
                    resultStates[extensionGroup][4] += stats[3]
                    resultStates[extensionGroup][5] += stats[4]
                    project_stats[id]["commits"][commit["short_id"]]["stats"]["files"][path] = stats
                    if debugmode: print(path + " : " + str(stats) + " [" + extensionGroup + "]")
                if debugmode: print("")
                if debugmode: print(resultStates)
                
                for key in resultStates:
                    project_stats[id]["commits"][commit["short_id"]]["stats"][key] = resultStates[key]
                
            else:
                print("E(" + str(commit["id"]) + "):" + str(response.status_code) )
        
                project_stats[id]["commits"][commit["short_id"]] = {
                "t": commit["title"], "a":autor, "d": commit["created_at"], "sa": add, "sd": deletions, "st" : stats, "sf" : fadd, "url" : commit["web_url"]
            }

    if(iProject >= save_each_projects or iCommit >= save_each_commits):
        SaveData()
        iProject = 0
        iCommit = 0
        sys.stdout.write(" #Saved# ")

    if(id >= max_proj): break

SaveData()
SaveRawData()

print("\nSaved all data completed!")

if(uploadGoogle and include_more_stats):
    UploadToGoogleSheets()


