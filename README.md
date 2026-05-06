# My trusted agent

This projects aims at implementing a minimalistic terminal-based AI agent that is cheap to run.

---

## Supported models

* DeepSeek
    * deepseek-v4-flash
    * deepseek-v4-pro

---

## Security

The AI agent does have support for tool calling, including the ability to execute any bash commands on the system.

However, for security reasons, all bash command needs to be manually approved by the user before being executed.

---

## How to run

### Setup

```shell
$ sudo apt update
$ sudo apt install -y python3-dev python3-pip python3-venv
```

### Run

```shell
$ bash ./run.sh
```
