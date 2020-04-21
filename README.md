# clashcli

A python cli tool for clash RESTful API.

## Install

```bash
git clone https://github.com/wangl-cc/clashcli.git
cd clashcli
# install in system direcory (may need root)
pip install .
# install in user direcory (recommd)
make install
# enable timer to update your subscription weekly
make timer
# install for user and enable timer
make install_all
```

## Usage

Change clash configs:

```
clashcli config -i <API_IP> -p <API_PORT>
```

Select proxy:

```
clashcli select -i <API_IP> -p <API_PORT>
```

Update subscription:

```
clashcli update -l <YOUR_SUBSCRIBE_URL> -c <PATH_TO_YOUR_CLASH_CONFIG_FILE>
```

Write configs to file:

```
clashcli write -i <API_IP> -p <API_PORT> -l <YOUR_SUBSCRIBE_URL> ...
```

Then you can just run without parameters:

```
clashcli config
clashcli select
clashcli update
```

The config file locate at `~/.config/clashcli/config.json`.

More Usage run `clashcli -h`.

<!-- vim modeline
vim:ts=2:sw=2:tw=75
-->
