#!/bin/bash

cd `dirname $0`/..

pip install -r requirements.txt
python ./db/init.py