# python-git-webhook
github-style webhook for arbitrary git repositories

Currently, this supports only push actions.

## How to use with gitolite v2:

Rename `webhook.py` to `update.secondary` and copy it to the hooks directory of your server-side repository.
Open the file, then scroll all the way to the bottom and find the line that says "ADD YOUR URL HERE".
Replace this by your webhook url.

## How to use without gitolite:

Rename `webhook.py` to `update` and copy it to the hooks directory of your server-side repository.
Replace the url as described above. Then find the lines that say
```
user_name = os.environ['GL_USER']
repo_name = os.environ['GL_REPO']
```
and replace the `os.environ[...]` parts with a user name and the name of your repository.

Alternatively, you can set the `GL_REPO` and `GL_USER` environment variables to some sensible values.

Also remove the lines that say

    check_gitolite_env('GL_USER')
    check_gitolite_env('GL_REPO')

# Tests

## Running the Tests

To run the test suite, simply run the webhook-test.py script.

## Writing Tests

The test framework operates on the gitlog -> json level because this has been
the cause of most bugs so far. Each test consists of a file containing a git log
and another file containing the expected output.

There are three modes of operation for the webhook script:
 1. Push to existing branch
 2. Creation of new branch
 3. Deletion of branch

The test suite does not cover the logic that detects which mode should be used
and instead requires you to explicitly specify the mode by encoding it in the
test file name. Tests must be named as follows:

 - `{TestName}.{Mode}.gitlog.txt` for the input git log.
 - `{TestName}.{Mode}.expected.json` for the expected json output.

Where `{TestName}` is an arbitrary name for the test that will be displayed in
the result overview and `{Mode}` is either `push`, `new` or `delete`.
