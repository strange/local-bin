#!/usr/bin/env python

"""
Quick and dirty script that generates an RSA key pair on a remote host, adds a
few lines to the ssh configuration and prints the public key to stdout.

I typically use this to setup a new server for use with gitosis [1]_::

    cd gitosis-admin-git-repo/ gitosis-keygen.py user@example.com \
        example2.com > keydir/example.pub

.. [1] http://eagain.net/gitweb/?p=gitosis.git

"""
import getpass
import optparse
import paramiko
import socket
import sys

# TODO: I usually run this script in an early stage before ssh access has been
# restricted to key-based authentication only. I should add functionality to
# login using a private key nevertheless.

# Consider rewriting this as a shell-script; void the dependency on paramiko.

class KeyFileExistsException(Exception):
    pass


def create_key(host, username, password, target_host, target_port,
               target_user, target_identifier):
    """Login to `host` via ssh. Once authenticated, create a passphrase-less
    key pair, add an entry with directions on how to connect to `target_host`
    in the ssh config and print the public key to stdout.
    
    The key pair is created in `~/.ssh/` on the targeted system. The
    filenames are derived from `target_identifier`.
    
    """
    private_key_filename = '~/.ssh/%s' % target_identifier
    public_key_filename = '%s.pub' % private_key_filename

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, password=password)

    # Test if file exists. ls prints one line to sterr for each pattern
    # that is not mathced. If sterr does not contain two lines, one or both
    # of the files that we are creating already exist.
    ls_command = 'ls %s %s' % (private_key_filename, public_key_filename)
    (stdin, stdout, stderr) = ssh.exec_command(ls_command)
    if len(stderr.readlines()) != 2:
        raise KeyFileExistsException

    # Genereate key pair (should have proper permissions set by default).
    keygen_command = 'ssh-keygen -t rsa -f %s -P \"\"' % private_key_filename
    (stdin, stdout, stderr) = ssh.exec_command(keygen_command)
    stdout.readlines()

    # Add entry to ssh config.
    interpolation_dict = {
        'target_host': target_host,
        'port': target_port,
        'target_user': target_user,
        'private_key_filename': private_key_filename,
    }
    add_config_command = ('echo -e "'
                          '\nHost %(target_host)s\n'
                          '\tHostName %(target_host)s\n'
                          '\tIdentityFile %(private_key_filename)s\n'
                          '\tPasswordAuthentication no\n'
                          '\tPort %(port)s\n'
                          '\tUser %(target_user)s\n\n'
                          '" >> ~/.ssh/config') % interpolation_dict
    (stdin, stdout, stderr) = ssh.exec_command(add_config_command)

    # Get public key content.
    cat_key_command = 'cat ~/.ssh/%s.pub' % target_identifier
    (stdin, stdout, stderr) = ssh.exec_command(cat_key_command)
    public_key = stdout.readlines()

    ssh.close()

    return "\n".join(public_key)

if __name__ == '__main__':
    parser = optparse.OptionParser(usage="Usage: %prog [options] <user@host> "
                                         "<target host>")
    parser.add_option('-u', '--target-user', dest='target_user',
                      help="User to add to ssh config for use when "
                           "connecting to the target host (default: git).")
    parser.add_option('-p', '--target-port', dest='target_port',
                      help="Port to add to ssh config for use when "
                           "connecting to the target host (default: 22).")
    parser.add_option('-t', '--target-identifier', dest='target_identifier',
                      help="Identifier for target host. Used as key "
                           "filename and as identifier in the ssh config "
                           "file (default: default).")
    parser.add_option('-P', '--password', dest='password')

    (opts, args) = parser.parse_args()

    if not len(args) == 2:
        parser.print_help()
        sys.exit(1)

    if not '@' in args[0]:
        parser.print_help()
        sys.exit(1)

    parts = args[0].split('@')
    if not len(parts) == 2:
        parser.print_usage()
        sys.exit(1)

    target_identifier = opts.target_identifier or 'default'
    target_port = opts.target_port or 22
    target_user = opts.target_user or 'git'

    user, host = (parts[0], parts[1])
    target_host = args[1]

    password = opts.password
    if password is None:
        text = 'Enter password for %s@%s: ' % (user, host)
        password = getpass.getpass(text, sys.stderr)

    try:
        pub_key = create_key(host, user, password, target_host, target_port,
                             target_user, target_identifier)
        print pub_key
    except paramiko.AuthenticationException, e:
        sys.stderr.write("%s\n" % e)
        sys.exit(2)
    except socket.gaierror, e:
        sys.stderr.write("%s\n" % e[1])
        sys.exit(2)
    except KeyFileExistsException, e:
        sys.stderr.write("One or more files that you are trying to create "
                         "already exist.\n")
        sys.exit(2)
