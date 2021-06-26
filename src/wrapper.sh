#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo $DIR
exec python3 "$DIR/check_auth.py" &
exec python3 "$DIR/processFrame.py" &
exec python3 "$DIR/mbus_server.py"
