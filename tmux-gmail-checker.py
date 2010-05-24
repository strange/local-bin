#!/usr/bin/env python
"""An extremly simple script that parses a local .muttrc and outputs a
tmux-formatted string displaying the total unread message count.

"""
import imaplib
import re
import sys

# The approach of parsing the credentials off of a configuration file might
# seem a little constipated, but I prefer not to give my password as an
# argument; I want to keep my "dotfiles" clear of sensitive information and
# it's nice to keep the stuff centralized. Do fork if you find it useful.

credentials_re = re.compile(r'set\s+imap_(user|pass)\s*=\s*"([^"]+)"')
def get_credentials(muttrc_path):
    """Return user-and-password-tuple by parsing a valid (containing the
    necessary credentials for connecting to an imap account) mutt
    configuration-file located at `muttrc_path`.
    
    """
    try:
        f = open(muttrc_path, 'r')
        data = f.read()
        f.close()
        credentials = dict(credentials_re.findall(data))
        return (credentials['user'], credentials['pass'])
    except KeyError:
        sys.stderr.write("Unable to parse credentials from muttrc file.\n")
        sys.exit(1)
    except IOError:
        sys.stderr.write("Unable to open muttrc file.\n")
        sys.exit(1)

def get_unread_count(server, username, password):
    try:
        c = imaplib.IMAP4_SSL(*server)
        c.login(username, password)
        c.select(readonly=1)
        (code, messages) = c.search('utf-8', 'UNSEEN')
        c.close()
        c.logout()
        if not len(messages):
            return 0
        return len(messages[0].split())
    except imaplib.IMAP4.error, e:
        sys.stderr.write("%s\n" % e.message)
        sys.exit(1)

def tmux_format(count):
    """Return message `count` formatted for use in the tmux statsubar."""
    if count == 0:
        return "No unread messages"
    s = count > 1 and 's' or ''
    return "#[bg=red,fg=white] %s unread message%s #[default]" % (count, s)

if __name__ == '__main__':
    if not len(sys.argv) > 1:
        sys.stderr.write("Usage: %s <path to .muttrc>\n" % sys.argv[0])
        sys.exit(1)

    (username, password) = get_credentials(' '.join(sys.argv[1:]))
    # Hardcoded to gmail as .. that is what I use and I do not keep the
    # host-part in my regular .muttrc.
    count = get_unread_count(('imap.gmail.com', 993), username, password)
    print tmux_format(count)
    sys.exit(0)
