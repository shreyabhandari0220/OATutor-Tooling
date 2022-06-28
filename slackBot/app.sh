#!/bin/bash

eval "$(conda shell.bash hook)"
conda activate slack_bot
python feedback_listener.py
