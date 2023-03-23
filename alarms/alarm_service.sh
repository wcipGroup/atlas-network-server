#!/bin/bash

filename="/srv/atlas-network-server/alarms/send_email.php"

m1=$(/bin/md5sum "$filename")
# echo $m1
while true; do

  # md5sum is computationally expensive, so check only once every 10 seconds
  sleep 10

  m2=$(/bin/md5sum "$filename")
  # echo $m2
  if [ "$m1" != "$m2" ] ; then
    # echo "File has changed!" >&2
    m1=$m2
    echo "Email sent successfully." >&2
    /bin/php /srv/atlas-network-server/alarms/send_email.php
  fi
done
