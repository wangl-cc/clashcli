import re
import os
import sys
import select
import json
from .api import ClashAPI

__all__ = ['ClashCLI', 'ClashCLIError']

CJK_CHAR_REGEX = r'[\u1100-\u11ff\u2e80-\u31ff\u3400-\u9FFF]'
#  r'\u16f00-\u1b2fff\u20000-\u2ebef\u2f800-\u2fa1f]'


class ClashCLIError(Exception):
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


class ClashCLI():
    def __init__(self, ip, port, auth=None):
        self.api = ClashAPI(ip, port, auth)
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

    def stream_print(self, stream, f):
        poll = select.epoll()
        poll.register(sys.stdin, select.EPOLLIN)
        while True:
            if stream.readable():
                f(json.loads(stream.readline()))
            poll_list = poll.poll(0.01)
            if len(poll_list) > 0:
                sys.stdin.read(1)
                break
        poll.close()
        self.api.close()

    def print_traffic(self):
        def traffic_print(d):
            print("up: {up:<15}  down:{down:<15}".format_map(d), end='\r')
        print('Realtime traffic (enter to quit):')
        stream = self.api.get_traffic()
        self.stream_print(stream, traffic_print)

    def print_log(self):
        def log_print(d):
            print("{type:<8}: {payload}".format_map(d))
        print('Realtime proxy logs (enter to quit):')
        stream = self.api.get_log()
        self.stream_print(stream, log_print)

    def list_proxies_delay(self):
        print("Begin delay test:")
        delay_dict = self.api.test_proxy_delay_all()
        self.align_print(['PROXY', 'Delay'], delay_dict)

    def list_selectors(self):
        selector_dict = self.api.get_selectors()
        return self.align_print(['Selector', 'Now'], selector_dict)

    def list_selector_opts(self, s):
        opt_dict = self.api.get_selector_opts(s)
        return self.align_print(['Proxy', 'Delay (ms)'], opt_dict, offset=10)

    def switch_proxy(self, s, p):
        status_code = self.api.switch_proxy(s, p)
        if status_code == 204:
            print('Selector update succeed!')
        elif status_code == 400:
            raise ClashCLIError('Proxy does not exist!')
        elif status_code == 404:
            raise ClashCLIError('Selector not found!')
        else:
            raise ClashCLIError('Unknown error code[{}]]'.format(status_code))

    def list_config(self):
        return self.align_print(['Config', 'Value'], self.api.configs)

    # Some error here, not work now
    #  def reload_config(self, *, force=False, path):
    #      status_code = self.api.reload_config(force=force, path=path)
    #      if status_code == 200 or status_code == 204:
    #          print('Reload succeed!')
    #      elif status_code == 400:
    #          raise ClashCLIError('Path error!')
    #      else:
    #          raise ClashCLIError('Unknown error!')

    def change_config(self, config, value):
        status_code = self.api.change_config(config, value)
        if status_code == 204:
            print('Config change succeed!')
        elif status_code == 400:
            raise ClashCLIError('Value error!')
        else:
            raise ClashCLIError('Unknown error!')

    def switch_proxy_cli(self):
        selectors = self.list_selectors()
        selector_n = check_input('Change which selector '
                                 '(number, empty to cancel): ', int)
        if selector_n <= 0:
            raise IndexError(selector_n)
        selector = selectors[selector_n-1]

        opts = self.list_selector_opts(selector)
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

        if re.search(r'port', config) is not None:
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
            raise ClashCLIError('This config is not suppurt now.')
        else:
            raise ClashCLIError('Unknown config.')
        self.change_config(config, value)

# vim:sw=4:ts=4:tw=75:ft=python
