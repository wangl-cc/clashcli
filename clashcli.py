#!/usr/bin/env python

import json
import http.client
import socket
import urllib.request
import re
import os
import argparse
import sys
import select


CJK_CHAR_REGEX = r'[\u1100-\u11ff\u2e80-\u31ff\u3400-\u9FFF]'
#  r'\u16f00-\u1b2fff\u20000-\u2ebef\u2f800-\u2fa1f]'


DEFALT_CLASH_CONFIG_PATH = os.path.expanduser(
    '~/.config/clash/config.yaml')
DEFALT_CLASH_CLI_CONFIG_DIR = os.path.expanduser(
    '~/.config/clashcli')
DEFALT_CLASH_CLI_CONFIG_FILE = os.path.expanduser(
    '~/.config/clashcli/config.json')
DEFALT_CLASH_CLI_CONFIG = {
    'ip': '127.0.0.1',
    'port': '9090',
    'url': '*',
    'clash': DEFALT_CLASH_CONFIG_PATH,
    'force': False
}


class ProxyError(Exception):
    pass


def align_cjk(string, *, length=4, align='<', fillchar=' '):
    cjk_chars = re.findall(CJK_CHAR_REGEX, string)
    string_len = len(string) + len(cjk_chars)
    dif = length - string_len
    if dif > 0:
        if align == '<':
            string = string + fillchar * dif
        elif align == '>':
            string = fillchar * dif + string
        elif align == '^':
            left = dif // 2
            right = dif - left
            string = fillchar * left + string + fillchar * right
        else:
            ValueError('Invalid alignment option.')

    return string


def check_input(prompt, parse_func):
    value = input(prompt)
    if value == '':
        sys.exit()
    return parse_func(value)


def str_to_bool(string):
    if string == '0':
        return False
    else:
        return True


class ClashInterop(object):
    def __init__(self, ip, port):
        self.conn = http.client.HTTPConnection(ip, port)

    def get(self, url):
        self.conn.request('GET', url)
        r = self.conn.getresponse()
        return json.load(r)

    def get_realtime(self, url, f):
        self.conn.request('GET', url)
        r = self.conn.getresponse()
        poll = select.epoll()
        poll.register(sys.stdin, select.EPOLLIN)
        while True:
            if r.readable():
                f(json.loads(r.readline()))
            poll_list = poll.poll(0.01)
            if len(poll_list) > 0:
                sys.stdin.read(1)
                break
        poll.close()
        self.conn.close()

    def put(self, url, *,
            headers={'Content-Type': 'application/json'}, data):
        self.conn.request('PUT', url, headers=headers,
                          body=json.dumps(data))
        return self.conn.getresponse().status

    def patch(self, url, *,
              headers={'Content-Type': 'application/json'}, data):
        self.conn.request('PATCH', url, headers=headers,
                          body=json.dumps(data))
        return self.conn.getresponse().status

    @property
    def proxies(self):
        proxies = self.get('/proxies')['proxies']
        self.proxies_static = proxies
        return proxies

    @property
    def configs(self):
        return self.get('/configs')

    def get_traffic(self, f):
        self.get_realtime('/traffic', f)

    def get_log(self, f):
        self.get_realtime('/logs', f)

    def get_proxies_by_type(self, t):
        proxies = []
        for k, v in self.proxies.items():
            if v['type'] == t:
                proxies.append(k)
        return proxies

    def get_proxy_delay(self, p):
        return self.proxies_static[p]['history'][-1]['delay']

    def list_selector(self):
        selectors = self.get_proxies_by_type('Selector')
        selectors_dict = {}
        for s in selectors:
            selectors_dict[s] = self.proxies[s]['now']
        return selectors_dict

    def selector_opt_with_delay(self, s):
        opt_list = self.proxies[s]['all']
        opt_dict = {}
        for opt in opt_list:
            if 'history' in self.proxies_static[opt] and\
                    len(self.proxies_static[opt]['history']) > 0:
                delay = self.get_proxy_delay(opt)
            elif self.proxies_static[opt]['type'] == 'URLTest':
                delay = self.get_proxy_delay(self.proxies_static[opt]['now'])
            else:
                delay = ' '
            if delay == 0:
                opt_dict[opt] = 'timeout'
            else:
                opt_dict[opt] = delay
        return opt_dict

    def switch_proxy(self, s, p):
        url = '/proxies/' + s
        data = {'name': p}
        return self.put(url, data=data)

    def change_config(self, config, value):
        data = {config: value}
        return self.patch('/configs', data=data)

    def change_config_by_dict(self, d):
        return self.patch('/configs', data=d)

    # Some error here, not work now
    def reload_config(self, *, force=False, path=DEFALT_CLASH_CONFIG_PATH):
        url = '/configs?force=' + json.dumps(force)
        data = {'path': path}
        return self.put(url, data=data)

    def close(self):
        return self.conn.close()

    def __exit__(self):
        return self.close()


class ClashCLI(ClashInterop):
    def __init__(self, ip, port):
        super().__init__(ip, port)
        columns = os.get_terminal_size().columns
        if columns >= 72:
            self.space = 30
        else:
            self.space = (columns-11)//2

    def align_print(self, names, values, *, offset=0):
        print(align_cjk('#'), align_cjk(names[0], length=self.space+offset),
              align_cjk(names[1], length=self.space-offset, align='>'),
              align_cjk('#', align='>'))
        i = 1
        key_list = []
        for k, v in values.items():
            print(align_cjk(str(i)),
                  align_cjk(str(k), length=self.space+offset),
                  align_cjk(str(v), length=self.space-offset, align='>'),
                  align_cjk(str(i), align='>'))
            i += 1
            key_list.append(k)
        return key_list

    def get_traffic(self):
        def print_traffic(d):
            print("up: {up:<15}  down:{down:<15}".format_map(d), end='\r')
        print('Realtime traffic (enter to quit):')
        super().get_traffic(print_traffic)

    def get_log(self):
        def print_log(d):
            print("{type:<8}: {payload}".format_map(d))
        print('Realtime proxy logs (enter to quit):')
        super().get_log(print_log)

    def list_selector(self):
        selector_dict = super().list_selector()
        return self.align_print(['Selector', 'Now'], selector_dict)

    def selector_opt_with_delay(self, s):
        opt_dict = super().selector_opt_with_delay(s)
        return self.align_print(['Proxy', 'Delay (ms)'], opt_dict, offset=10)

    def switch_proxy(self, s, p):
        status_code = super().switch_proxy(s, p)
        if status_code == 204:
            print('Selector update succeed!')
        elif status_code == 400:
            raise ProxyError('Proxy does not exist!')
        elif status_code == 404:
            raise ProxyError('Selector not found!')
        else:
            raise ProxyError('Unknown error code[{}]]'.format(status_code))

    def list_config(self):
        return self.align_print(['Config', 'Value'], self.configs)

    # Some error here, not work now
    def reload_config(self, *, force=False, path=DEFALT_CLASH_CONFIG_PATH):
        status_code = super().reload_config(force=force, path=path)
        if status_code == 200 or status_code == 204:
            print('Reload succeed!')
        elif status_code == 400:
            raise ProxyError('Path error!')
        else:
            raise ProxyError('Unknown error!')

    def change_config(self, config, value):
        status_code = super().change_config(config, value)
        if status_code == 204:
            print('Config change succeed!')
        elif status_code == 400:
            raise ProxyError('Value error!')
        else:
            raise ProxyError('Unknown error!')

    def switch_proxy_cli(self):
        selectors = self.list_selector()
        selector_n = check_input('Change which selector '
                                 '(number, empty to cancel): ', int)
        if selector_n <= 0:
            raise IndexError(selector_n)
        selector = selectors[selector_n-1]

        opts = self.selector_opt_with_delay(selector)
        proxy_n = check_input('Switch ' + selector + ' to which proxy '
                              '(number, empty to cancel): ', int)
        if proxy_n <= 0:
            raise IndexError(proxy_n)
        proxy = opts[proxy_n-1]
        self.switch_proxy(selector, proxy)

    def change_config_cli(self):
        configs = self.list_config()
        config_n = check_input('Change which config '
                               '(number, empty to cancel): ', int)
        if config_n <= 0:
            raise IndexError(config_n)
        config = configs[config_n-1]

        if not re.search(r'port', config) is None:
            value = check_input('Change ' + config + ' to which port '
                                '(number, empty to cancel): ', int)
        elif config == 'allow-lan':
            value = check_input('Allow-lan (1 for true, '
                                '0 for Flase, empty to cancel): ',
                                str_to_bool)
        elif config == 'mode':
            value = check_input('Change to which mode (Rule/Global/'
                                'Direct, empty to cancel): ', str)
        elif config == 'log-level':
            value = check_input('Change to which level (info/warning/ '
                                'error/debug/silent, empty to cancel): ',
                                str)
        elif config == 'bind-address':
            value = check_input('Change to which address '
                                '(ip address or *, empty to cancel): ',
                                str)
        elif config == 'authentication':
            raise ProxyError('This config is not suppurt now.')
        else:
            raise ProxyError('Unknown config.')
        self.change_config(config, value)


def update_subscrice(url, target):
    download = urllib.request.urlopen(url)
    if download.status != 200:
        return download.status
    with open(target, 'w') as io:
        for line in download.readlines():
            line = line.decode('utf-8')
            if not re.match(r'external-controller: .*', line) is None:
                line = "external-controller: {ip}:{port}\n".format_map(
                    arg_dict)
            io.write(line)
    return 200


parser = argparse.ArgumentParser(
    description='A simple cli tool to manage clash.'
)
parser.add_argument('action', help="""
                    config (Change clash config);
                    select (Select proxy);
                    update (Update subscribe);
                    traffic (Get real time traffic);
                    log (Get real time logs)
                    write (Write arguments to file).
                    """,
                    #  reload (Reload config file);
                    type=str, choices=['config', 'select', 'update',
                                       'traffic', 'log', 'write']
                    )
parser.add_argument('-i', '--ip', type=str,
                    help='Clash RESTful API ip.')
parser.add_argument('-p', '--port', type=int,
                    help='Clash RESTful API port.')
parser.add_argument('-c', '--clash', type=str,
                    default=os.path.expanduser(
                        '~/.config/clash/config.yaml'),
                    help='Clash config file location'
                    'for reload and update.')
parser.add_argument('-l', '--url', type=str,
                    help='Subscribe url.')
parser.add_argument('-f', '--force', action='store_true',
                    help='Reload with force flag.')
args = parser.parse_args()

arg_dict = vars(args)

# create config file
if not os.path.exists(DEFALT_CLASH_CLI_CONFIG_DIR):
    print('Create config file at', DEFALT_CLASH_CLI_CONFIG_FILE)
    os.mkdir(DEFALT_CLASH_CLI_CONFIG_DIR)
    with open(DEFALT_CLASH_CLI_CONFIG_FILE, 'w') as io:
        json.dump(DEFALT_CLASH_CLI_CONFIG, io)
elif not os.path.exists(DEFALT_CLASH_CLI_CONFIG_FILE):
    print('Create config file at', DEFALT_CLASH_CLI_CONFIG_FILE)
    with open(DEFALT_CLASH_CLI_CONFIG_FILE, 'w') as io:
        json.dump(DEFALT_CLASH_CLI_CONFIG, io)

# set default opts
with open(DEFALT_CLASH_CLI_CONFIG_FILE, 'r') as io:
    default_dict = json.load(io)
    for k, v in default_dict.items():
        if arg_dict[k] is None:
            arg_dict[k] = v

if arg_dict['action'] == 'update':
    if arg_dict['url'] != '*':
        code = update_subscrice(arg_dict['url'], arg_dict['clash'])
        if code != 200:
            sys.exit('Download file error, code[{}]'.format(code))
        else:
            sys.exit()
    else:
        sys.exit('Specify your subscribe url to get clash config.')
elif arg_dict['action'] == 'write':
    arg_dict.pop('action')
    with open(DEFALT_CLASH_CLI_CONFIG_FILE, 'w') as io:
        json.dump(arg_dict, io)
    sys.exit()

try:
    cli = ClashCLI(arg_dict['ip'], arg_dict['port'])
    if arg_dict['action'] == 'config':
        cli.change_config_cli()
    elif arg_dict['action'] == 'select':
        cli.switch_proxy_cli()
    elif arg_dict['action'] == 'reload':
        cli.reload_config(force=arg_dict['force'],
                          path=arg_dict['clash'])
    elif arg_dict['action'] == 'traffic':
        cli.get_traffic()
    elif arg_dict['action'] == 'log':
        cli.get_log()
except socket.timeout:
    sys.exit('Connection timeout, make sure your clash is running '
             'and you ip and port is correct.')
except IndexError:
    sys.exit('Select out of range!')
except ProxyError as e:
    sys.exit(*e.args)
except Exception:
    raise

sys.exit()

# vim:sw=4:ts=4:tw=75:ft=python
