from .cli import ClashCLI
import urllib.request
import argparse
import sys
import os
import json

DEFAULT_CLASH_CONFIG_PATH = os.path.expanduser(
    '~/.config/clash/config.yaml')
DEFAULT_CLASH_CLI_CONFIG_DIR = os.path.expanduser(
    '~/.config/clashcli')
DEFAULT_CLASH_CLI_CONFIG_FILE = os.path.expanduser(
    '~/.config/clashcli/config.json')
DEFAULT_CLASH_CLI_CONFIG = {
    'ip': '127.0.0.1',
    'port': '9090',
    'secret': None,
    'url':  None,
    'clash': DEFAULT_CLASH_CONFIG_PATH,
    #  'force': False
}


def get_default_config(args, *params):
    default_config = DEFAULT_CLASH_CLI_CONFIG.copy()
    if os.path.exists(DEFAULT_CLASH_CLI_CONFIG_FILE):
        with open(DEFAULT_CLASH_CLI_CONFIG_FILE, 'r') as io:
            default_config.update(json.load(io))
    args_dict = vars(args)
    ret = []
    for param in params:
        if args_dict[param] is None:
            ret.append(default_config[param])
        else:
            ret.append(args_dict[param])
    return ret


def update(args):
    """
    Update your subscribe.
    """
    url, target = get_default_config(args, 'url', 'clash')
    download = urllib.request.urlopen(url)
    code = download.status
    if code != 200:
        sys.exit('Download file error, code[{}]'.format(code))
    else:
        with open(target, 'w') as io:
            io.write(download.read().decode('utf-8'))


def config(args):
    """
    Change Clash configuration.
    """
    ip, port, secret = get_default_config(args, 'ip', 'port', 'secret')
    cli = ClashCLI(ip, port, secret)
    cli.change_config_cli()


def test(args):
    """
    Test proxies delay.
    """
    ip, port, secret = get_default_config(args, 'ip', 'port', 'secret')
    cli = ClashCLI(ip, port, secret)
    cli.list_proxies_delay()


def select(args):
    """
    Select proxy for selectors.
    """
    ip, port, secret = get_default_config(args, 'ip', 'port', 'secret')
    cli = ClashCLI(ip, port, secret)
    cli.switch_proxy_cli()


def log(args):
    """
    Show Clash logs.
    """
    ip, port, secret = get_default_config(args, 'ip', 'port', 'secret')
    cli = ClashCLI(ip, port, secret)
    cli.print_log()


def traffic(args):
    """
    Show your proxy traffic.
    """
    ip, port, secret = get_default_config(args, 'ip', 'port', 'secret')
    cli = ClashCLI(ip, port, secret)
    cli.print_traffic()


def write(args):
    """
    Write configs to file.
    """
    default_config = DEFAULT_CLASH_CLI_CONFIG.copy()
    if not os.path.exists(DEFAULT_CLASH_CLI_CONFIG_DIR):
        os.mkdir(DEFAULT_CLASH_CLI_CONFIG_DIR)
    elif os.path.exists(DEFAULT_CLASH_CLI_CONFIG_FILE):
        with open(DEFAULT_CLASH_CLI_CONFIG_FILE, 'r') as io:
            default_config.update(json.load(io))

    for k, v in vars(args).items():
        if v is not None:
            default_config[k] = v

    default_config.pop('func')
    with open(DEFAULT_CLASH_CLI_CONFIG_FILE, 'w') as io:
        json.dump(default_config, io)


def main():
    parser = argparse.ArgumentParser(prog='clashcli')
    subparser = parser.add_subparsers()
    for f in (config, select, traffic, log, test):
        p = subparser.add_parser(f.__name__, help=f.__doc__)
        p.add_argument('-i', '--ip', type=str,
                       help='Clash RESTful API ip.')
        p.add_argument('-r', '--port', type=str,
                       help='Clash RESTful API port.')
        p.add_argument('-s', '--secret', type=str,
                       help='Clash RESTful API secret.')
        p.set_defaults(func=f)

    p = subparser.add_parser('update', help=update.__doc__)
    p.add_argument('-c', '--clash', type=str,
                   help='Clash config file location '
                   'for update target.')
    p.add_argument('-l', '--url', type=str,
                   help='Subscribe url.')
    p.set_defaults(func=update)

    p = subparser.add_parser('write', help=write.__doc__)
    p.add_argument('-i', '--ip', type=str,
                   help='Clash RESTful API ip.')
    p.add_argument('-r', '--port', type=str,
                   help='Clash RESTful API port.')
    p.add_argument('-s', '--secret', type=str,
                   help='Clash RESTful API secret.')
    p.add_argument('-c', '--clash', type=str,
                   help='Clash config file location '
                   'for update target.')
    p.add_argument('-l', '--url', type=str,
                   help='Subscribe url.')
    p.set_defaults(func=write)

    args = parser.parse_args()

    if 'func' in vars(args):
        args.func(args)
    else:
        parser.parse_args(['-h'])

# vim:sw=4:ts=4:tw=75:ft=python
