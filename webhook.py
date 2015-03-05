#!/usr/bin/python
import subprocess
import json
import sys
import os
import urllib2
import functools

# globals
lineNr = 0

def send_json_post(url, payload):
    json_payload = json.dumps(payload)
    urllib2.urlopen(url, json_payload)


def webhook_post(url, oldrev, newrev, refname, repo_name, user_name):
    # we work with a callback here to make the webhook_post_* functions more easily testable
    callback = functools.partial(send_json_payload, url=url)

    # we need to distinguish between special cases where branches are created or deleted
    # because in those cases we cannot use the normal git log and the result looks very different

    if len(oldrev.strip('0')) == 0:
        gitlog = subprocess.check_output('git log --name-status ' + newrev + ' --not --branches=*', shell=True)
        webhook_post_newbranch(gitlog, newrev, refname, repo_name, user_name, callback)

    elif len(newrev.strip('0')) == 0:
        webhook_post_deletebranch(refname, repo_name, user_name, callback)

    else:
        gitlog = subprocess.check_output('git log --name-status ' + oldrev + '..' + newrev, shell=True)
        webhook_post_push(gitlog, oldrev, newrev, refname, repo_name, user_name, callback)


def webhook_post_push(gitlog, oldrev, newrev, refname, repo_name, user_name, callback):
    commits = parse_gitlog(gitlog)
    if len(commits) == 0:
        raise Exception('git log returned no commits')
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
    callback(payload=payload)

def webhook_post_newbranch(gitlog, newrev, repo_name, user_name, callback):
    commits = parse_gitlog(gitlog)
    payload = {
        'ref': refname,
        'after': newrev,
        'created': True,
        'deleted': False,
        'forced': False,
        'commits': commits,
        'repository': {
            'name': repo_name
        },
        'pusher': {
            'name': user_name
        }
    }
    if len(commits) > 0:
        payload['head_commit'] = commits[0]

    callback(payload=payload)

def webhook_post_deletebranch(refname, repo_name, user_name, callback):
    payload = {
        'ref': refname,
        'created': False,
        'deleted': True,
        'forced': False,
        'commits': [],
        'repository': {
            'name': repo_name
        },
        'pusher': {
            'name': user_name
        }
    }
    callback(payload=payload)

def get_commits(oldrev, newrev):
    gitlog = subprocess.check_output('git log --name-status ' + oldrev + '..' + newrev, shell=True)
    commits = parse_gitlog(gitlog)
    return commits

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

    # Handle the commit headers, some of which may be missing in some cases:
    if gitlog[0].startswith('Merge'):
        parse_commit_merge(commit, gitlog)
    if gitlog[0].startswith('Author'):
        parse_commit_author(commit, gitlog)
    if gitlog[0].startswith('Date'):
        parse_commit_date(commit, gitlog)

    skip_newline(gitlog)
    parse_commit_message(commit, gitlog)

    # There is not always a file section (e.g. merge commits without conflicts)
    if is_commit_file_line(gitlog[0]):
        parse_commit_files(commit, gitlog)
    return commit

def parse_commit_firstline(commit, gitlog):
    global lineNr
    lineNr += 1
    words = gitlog.pop(0).split()
    if words[0] != 'commit':
        error("expected begin of commit, but found '" + words[0] + "' in line " + str(lineNr))
    commit['id'] = words[1]

def parse_commit_merge(commit, gitlog):
    # we just ignore the Merge: line
    global lineNr
    lineNr += 1
    gitlog.pop(0)

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
    while len(gitlog[0]) == 0 or gitlog[0].startswith('    '):
        lineNr += 1
        line = gitlog.pop(0)
        commit['message'] += line.strip() + os.linesep
        if len(gitlog) == 0:
            return

def is_commit_file_line(line):
    if len(line) == 0:
        return False
    if not (line[0] == 'M' or line[0] == 'A' or line[0] == 'D'):
        return False
    if not (line[1:].startswith('    ')):
        return False
    return True

def parse_commit_files(commit, gitlog):
    global lineNr
    commit['added'] = []
    commit['removed'] = []
    commit['modified'] = []
    lineNr += 1
    line = gitlog.pop(0)
    while line != '':
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

def check_gitolite_env(env_var_name):
    if not env_var_name in os.environ:
        print 'Error posting webhook: '
        print '    environment variable ' + env_var_name + ' is not defined'
        print '    if you are not using gitolite, please define it yourself or modify this script'
        print 'This error does not mean that your push failed.'
        sys.exit()

if __name__=='__main__':
    if len(sys.argv) < 4:
        print 'Error posting webhook: '
        print '    not enough parameters given to script -- are you sure you registered this as an update hook?'
        print '    arguments: '
        for arg in sys.argv:
            print '        ' + str(i) + ': "' + arg + '"'
        print 'This error does not mean that your push failed.'
        sys.exit()

    check_gitolite_env('GL_USER')
    check_gitolite_env('GL_REPO')

    refname = sys.argv[1]
    oldrev = sys.argv[2]
    newrev = sys.argv[3]
    user_name = os.environ['GL_USER']
    repo_name = os.environ['GL_REPO']

    url = "ADD YOUR URL HERE"

    try:
        webhook_post(url, oldrev, newrev, refname, repo_name, user_name)
    except:
        ex = sys.exc_info()[0]
        print 'Error posting webhook: '
        print '    refname: ' + refname
        print '    oldrev: ' + oldrev
        print '    newrev: ' + newrev
        print ex
        print
        print 'This error does not mean that your push failed.'
