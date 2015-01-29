#!/usr/bin/python
import subprocess
import json
import sys
import os
import urllib2

def webhook_post(url, oldrev, newrev, refname, repo_name, user_name):
    commits = get_commits(oldrev, newrev)
    payload = {
        'ref': refname,
        'before': oldrev,
        'after': newrev,
        'created': False,
        'deleted': False,
        'forced': False,
        'commits': commits,
        'head_commit': commits[0],
        'repository': {
            'name': repo_name
        },
        'pusher': {
            'name': user_name
        }
    }
    json_payload = json.dumps(payload)
    u = urllib2.urlopen(url, json_payload)

def get_commits(oldrev, newrev):
    gitlog = subprocess.check_output('git log --name-status ' + oldrev + '..' + newrev, shell=True)
    commits = parse_gitlog(gitlog)
    return commits

lineNr = 0

def parse_gitlog(gitlog_output):
    global lineNr
    lineNr = 0
    gitlog = gitlog_output.splitlines()
    commits = []
    while len(gitlog) > 0:
        commit = parse_commit(gitlog)
        commits.append(commit)
    return commits
        
def parse_commit(gitlog):
    commit = {}
    parse_commit_firstline(commit, gitlog)
    if gitlog[0].strip().startswith('Author'):
        parse_commit_author(commit, gitlog)
        parse_commit_date(commit, gitlog)
        skip_newline(gitlog)
    parse_commit_message(commit, gitlog)
    parse_commit_files(commit, gitlog)
    return commit

def parse_commit_firstline(commit, gitlog):
    global lineNr
    lineNr += 1
    words = gitlog.pop(0).split()
    if words[0] != 'commit':
        error("expected begin of commit, but found '" + words[0] + "' in line " + str(lineNr))
    commit['id'] = words[1]

def parse_commit_author(commit, gitlog):
    global lineNr
    lineNr += 1
    line = gitlog.pop(0)
    if not line.startswith('Author: '):
        error("expected Author or Merge line of commit, but found '" + line + "' in line " + str(lineNr))

    email_start = line.find('<')
    email_end = line.find('>')
    commit['author'] = {}
    if email_start > 0 and email_end > 0:
        commit['author']['name'] = line[8:email_start].strip()
        commit['author']['email'] = line[email_start+1:email_end]
    else:
        commit['author']['name'] = line[8:]
        commit['author']['email'] = ''

    return True

def parse_commit_date(commit, gitlog):
    global lineNr
    lineNr += 1
    line = gitlog.pop(0)
    if not line[0:6] == 'Date: ':
        error("expected Date line of commit, but found '" + line + "' in line " + str(lineNr))
    commit['timestamp'] = line[6:].strip()

def skip_newline(gitlog):
    global lineNr
    lineNr += 1
    line = gitlog.pop(0)
    if not line.strip() == '':
        error("expected whitespace at line " + str(lineNr) + " but found: " + line)

def parse_commit_message(commit, gitlog):
    global lineNr
    commit['message'] = ''
    lineNr += 1
    line = gitlog.pop(0)
    while line.strip() != '':
        commit['message'] += line.strip() + os.linesep
        if len(gitlog) == 0:
            return
        lineNr += 1
        line = gitlog.pop(0)

def parse_commit_files(commit, gitlog):
    global lineNr
    commit['added'] = []
    commit['removed'] = []
    commit['modified'] = []
    lineNr += 1
    line = gitlog.pop(0)
    while line.strip() != '':
        if line[:1] == 'M':
            commit['modified'].append(line[1:].strip())
        elif line[:1] == 'A':
            commit['added'].append(line[1:].strip())
        elif line[:1] == 'D':
            commit['removed'].append(line[1:].strip())

        if len(gitlog) == 0:
            return
        lineNr += 1
        line = gitlog.pop(0)

def error(msg):
    print msg
    exit(1)

if __name__=='__main__':
    refname = sys.argv[1]
    oldrev = sys.argv[2]
    newrev = sys.argv[3]
    user_name = os.environ['GL_USER']
    repo_name = os.environ['GL_REPO']

    url = "ADD YOUR URL HERE"
    
    webhook_post(url, oldrev, newrev, refname, repo_name, user_name)
