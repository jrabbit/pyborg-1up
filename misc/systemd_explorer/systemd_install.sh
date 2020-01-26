#!/bin/bash

install ./*.service /usr/lib/systemd/system
systemctl reload-daemon
systemctl enable pyborg_*
journalctl