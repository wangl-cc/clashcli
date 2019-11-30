# clashcli

A python cli tool for clash RESTful API.

## Install

```
git clone https://github.com/wangl-cc/clashcli.git
cd clashcli
pip install .
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

Update subscribe:

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
