#!/usr/bin/env python3
# vim: set expandtab shiftwidth=4:
# -*- Mode: python; coding: utf-8; indent-tabs-mode: nil -*- */
#
# This script tests a few things against the commit messages, search for
# `def test_` to see the actual tests run.

import git
import os
import pytest

# Environment variables set by gitlab
CI_COMMIT_SHA = os.environ['CI_COMMIT_SHA']
CI_MERGE_REQUEST_TARGET_BRANCH_NAME = 'master'
CI_SERVER_HOST = os.environ['CI_SERVER_HOST']

# We need to add the real libinput as remote, our origin here is the user's
# fork.
repo = git.Repo('.')
if 'upstream' not in repo.remotes:
    upstream = repo.create_remote('upstream', f'https://{CI_SERVER_HOST}/libinput/libinput.git')
    upstream.fetch()

sha = CI_COMMIT_SHA
branch = CI_MERGE_REQUEST_TARGET_BRANCH_NAME

commits = list(repo.iter_commits(f'upstream/{branch}..{sha}'))


def error(commit, message, long_message=''):
    info = ('After correcting the above issue(s), force-push to the same branch.\n'
            'This will re-trigger the CI.\n\n'
            'A list of requirements for commit messages is available at\n'
            'https://gitlab.freedesktop.org/libinput/libinput/blob/master/CODING_STYLE.md')

    msg = (f'\n'
           f'Commit message check failed: {message}\n\n'
           f'  commit: {str(commit)}\n'
           f'  author: {commit.author.name} <{commit.author.email}>\n'
           f'\n'
           f'  {commit.summary}\n'
           f'\n'
           f'\n'
           f'{long_message}\n\n'
           f'{info}\n\n')
    return msg

@pytest.mark.parametrize('commit', commits)
class TestCommits:
    def test_author_email(self, commit):
        assert '@users.noreply.gitlab.freedesktop.org' not in commit.author.email, \
            error(commit, 'git author email invalid',
                  ('Please set your name and email with the commands\n',
                   '    git config --global user.name Your Name\n'
                   '    git config --global user.email your.email@provider.com\n'))

    def test_signed_off_by(self, commit):
        if not commit.message.startswith('Revert "'):
            assert 'Signed-off-by:' in commit.message, \
                error(commit, 'missing Signed-off-by tag',
                      'Please add the required "Signed-off-by: author information" line\n'
                      'to the commit message')

    def test_fixup(self, commit):
        assert not commit.message.startswith('fixup!'), \
            error(commit, 'Remove fixup! tag',
                  'Leftover "fixup!" commit message detected, please squash')
        assert not commit.message.startswith('squash!'), \
            error(commit, 'Remove squash! tag',
                  'Leftover "squash!" commit message detected, please squash')

    def test_line_length(self, commit):
        lines = commit.message.split('\n')
        first_line = lines[0]

        assert len(first_line) < 85, \
            error(commit, 'Commit message subject line too long')

        try:
            second_line = lines[1]
            assert second_line == '', \
                error(commit, 'Second line in commit message must be emtpy')
        except IndexError:
            pass
