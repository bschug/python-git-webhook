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
