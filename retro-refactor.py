#!/usr/bin/python

import argparse
import sys
import shlex
from pipes import quote
from subprocess import check_call, check_output
from textwrap import dedent

def replacements(x):
    if len(x) % 2 != 0:
        raise RuntimeError('Must have an even number of arguments')
    try:
        i = iter(x)
        while True:
            yield (i.next(), i.next())
    except StopIteration:
        return

def main(argv):
    head = check_output(['git', 'symbolic-ref', 'HEAD']).strip()
    if not head.startswith('refs/heads/'):
        sys.stderr.write("ERROR: Detatched head")
        return 1

    default_branch = head[len('refs/heads/'):]

    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='master')
    parser.add_argument('-b', '--branch', default=default_branch)
    parser.add_argument('replacements', nargs='*')
    parser.add_argument('-n', '--dry-run', action='store_true')
    args = parser.parse_args(argv[1:])

    if args.dry_run:
        call = lambda cmd: sys.stderr.write(' '.join([quote(x) for x in cmd])
                                            + '\n')
    else:
        call = check_call

    oldref = 'refs/heads/' + args.branch
    newref = 'refs/retro-refactor/' + args.branch

    r = list(replacements(args.replacements))
    if len(r) == 0:
        raise RuntimeError('No replacements specified')

    grep_cmdline = ['git', 'grep', '-l', '-z']
    for a, _ in r:
        grep_cmdline += ['-e', a]
    sed_cmds = []
    for a, b in r:
        sed_cmds += ['-e', 's/%s/%s/g' % (a.replace('/', '\/'), b.replace('/', '\/'))]
    sed_quoted = ' '.join([quote(x) for x in sed_cmds])

    rename_cmd = dedent("""\
        git ls-files %s | while read filename;
        do
            newname="$(echo $filename | sed %s)" &&
            mkdir -p "$(dirname "$newname")" &&
            mv "$filename" "$newname";
        done""").replace('\n', ' ') % (
            ' '.join([quote('*%s*' % x) for x, _ in r]),
            sed_quoted
        )

    tree_filter = ' '.join([quote(x) for x in grep_cmdline] +
                           ['|', 'xargs', '--no-run-if-empty', '-0', 'sed', '--in-place'] +
                           [quote(x) for x in sed_cmds] + ['&& ']) + \
                  rename_cmd
    msg_filter = ' '.join(['sed'] + [quote(x) for x in sed_cmds])

    call([
        'git', 'update-ref', '-m', 'retro-refactor', newref, oldref])
    call([
        'git', 'filter-branch', '-f',
        '--tree-filter', tree_filter,
        '--msg-filter', msg_filter,
        '--original', 'refs/original/retro-refactor',
        "%s..%s" % (args.base, newref)])

    call(['git', 'diff', '-M', oldref, newref])
    sys.stderr.write(dedent("""\
        If you're happy with your changes apply them with:
        
            git reset --hard %s
        """) % newref)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
