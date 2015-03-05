from __future__ import print_function
import os
import functools
import json

import webhook

def eval_test(test_name, expected, payload):
    actual = json.dumps(payload, indent=4, sort_keys=True)

    if expected != actual:
        print(test_name + " Test failed: ")
        print("Expected:")
        print(expected)
        print()
        print("Actual:")
        print(actual)
        print()
    else:
        print(test_name + ' OK')

def test(test_name):
    webhook.lineNr = 0

    with open("test/" + test_name + ".gitlog.txt") as f:
        gitlog = f.read()
    with open("test/" + test_name + ".expected.json") as f:
        expected = f.read()
        try:
            expected = json.dumps(json.loads(expected), indent=4, sort_keys=True)
        except:
            pass

    callback = functools.partial(eval_test, test_name=test_name, expected=expected)

    if test_name.endswith('.push'):
        webhook.webhook_post_push(gitlog, "my_oldrev", "my_newrev", "my_refname", "my_repo_name", "my_user_name", callback)
    elif test_name.endswith('.new'):
        webhook.webhook_post_newbranch(gitlog, "my_newrev", "my_repo_name", "my_user_name", callback)
    elif test_name.endswith('.delete'):
        webhook.webhook_post_deletebranch("my_refname", "my_repo_name", "my_user_name", callback)


if __name__ == '__main__':
    for filename in os.listdir("test"):
        if filename.endswith('.gitlog.txt'):
            testname = filename[:-len('.gitlog.txt')]
            test(testname)
