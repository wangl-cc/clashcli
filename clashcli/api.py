import http.client
import json
from urllib.parse import quote

PRXOY_TYPE = ('Direct', 'Reject', 'Shadowsocks', 'Vmess', 'Socks', 'Http')

GROUP_TYPE = ('Selector', 'URLTest', 'Fallback')


class ClashAPI(object):
    def __init__(self, ip, port, auth=None):
        self.conn = http.client.HTTPConnection(ip, port)
        if auth is not None:
            self.headers = {'Authorization': 'Bearer' + auth}
        else:
            self.headers = {}

    def get_stream(self, url, params=None):
        if params is not None:
            url += '?'
            for k, v in params.items():
                url += k + '=' + str(v) + '&'
            url = url[0:-1]
        self.conn.request('GET', url, headers=self.headers)
        return self.conn.getresponse()

    def get(self, url, params=None):
        r = self.get_stream(url, params)
        return json.load(r)

    def put(self, url, *,
            headers={'Content-Type': 'application/json'}, data):
        headers = headers.copy()
        headers.update(self.headers)
        self.conn.request('PUT', url, headers=headers,
                          body=json.dumps(data))
        return self.conn.getresponse().status

    def patch(self, url, *,
              headers={'Content-Type': 'application/json'}, data):
        headers = headers.copy()
        headers.update(self.headers)
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

    def get_traffic(self):
        return self.get_stream('/traffic')

    def get_log(self):
        return self.get_stream('/logs')

    def get_proxies_by_type(self, t):
        proxies = []
        for k, v in self.proxies.items():
            if v['type'] == t:
                proxies.append(k)
        return proxies

    def get_proxy_delay(self, p):
        if self.proxies_static[p]['type'] in PRXOY_TYPE:
            delay = self.proxies_static[p]['history'][-1]['delay']
            if delay == 0:
                return 'Timeout'
            else:
                return delay
        elif self.proxies_static[p]['type'] in GROUP_TYPE:
            return self.get_proxy_delay(self.proxies_static[p]['now'])
        else:
            return 'Unknown Proxy'

    def test_proxy_delay(self, p):
        url = '/proxies/' + quote(p) + '/delay'
        params = {
            'timeout': 2000,
            'url': 'http://www.gstatic.com/generate_204'
        }
        return self.get(url, params)

    def test_proxy_delay_all(self):
        delay_dict = {}
        for k, v in self.proxies.items():
            if v['type'] in PRXOY_TYPE:
                _, t = self.test_proxy_delay(k).popitem()
                if t == 'An error occurred in the delay test':
                    delay_dict[k] = 'Test error'
                else:
                    delay_dict[k] = t

        return delay_dict

    def get_selectors(self):
        selectors = self.get_proxies_by_type('Selector')
        selectors_dict = {}
        for s in selectors:
            selectors_dict[s] = self.proxies[s]['now']
        return selectors_dict

    def get_selector_opts(self, s):
        opt_list = self.proxies[s]['all']
        opt_dict = {}
        for opt in opt_list:
            opt_dict[opt] = self.get_proxy_delay(opt)
        return opt_dict

    def get_rules(self):
        return self.get('/rules')['rules']

    def update_rules(self):
        return self.put('/rules', headers={}, data=None)

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
    #  def reload_config(self, *, force=False, path):
    #      url = '/configs?force=' + json.dumps(force)
    #      data = {'path': path}
    #      return self.put(url, data=data)

    def close(self):
        return self.conn.close()

    def __exit__(self):
        return self.close()

# vim:sw=4:ts=4:tw=75:ft=python
