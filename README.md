git retro-refactor
==================

Applies a sed find/replace to git history using `git filter-branch`.  Useful if
you want to retroactively rename a file or fix a typo.  Performs substitutions
on filenames, commit messages and in the content.

Usage:

    git retro-refactor search_term replacement

Installation
------------

Run

    git config --global alias.retro-refactor '!/path/to/retro-refactor.py'

Dependencies
------------

* git
* Python

Licence
-------

GPLv2+
