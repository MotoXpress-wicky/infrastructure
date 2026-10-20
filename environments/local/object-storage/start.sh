#!/bin/sh

set -eu
weed server -dir=/data -s3 -s3.port=8333 &
server_pid=$!

# When Docker stops the container, stop the server cleanly.
trap 'kill -TERM "$server_pid" 2>/dev/null; wait "$server_pid"; exit 0' TERM INT

# weed shell reads its commands from standard input.
shell() { echo "$1" | weed shell; }

echo "object-storage: waiting for the server"
until wget -q -O /dev/null http://127.0.0.1:9333/cluster/status \
   && wget -q -O /dev/null http://127.0.0.1:8888/; do
  sleep 2
done


clean() { tr -d '\r' < "$1" | grep -v '^[[:space:]]*#' | grep -v '^[[:space:]]*$' || true; }

clean /setup/buckets.conf > /tmp/buckets
existing=$(shell "s3.bucket.list")
while read -r bucket access; do
  if ! echo "$existing" | grep -qw "$bucket"; then
    echo "object-storage: creating bucket $bucket"
    shell "s3.bucket.create -name $bucket"
  fi
  if [ "$access" = "public" ]; then
    shell "s3.bucket.access -name $bucket -user anonymous -access Read"
  fi
done < /tmp/buckets

clean /setup/users.conf > /tmp/users
while read -r user prefix buckets; do
  eval "access_key=\${${prefix}_ACCESS_KEY:-}"
  eval "secret_key=\${${prefix}_SECRET_KEY:-}"
  if [ -z "$access_key" ] || [ -z "$secret_key" ]; then
    echo "object-storage: ${prefix}_ACCESS_KEY or ${prefix}_SECRET_KEY missing in env/object-storage.env"
    kill -TERM "$server_pid"
    exit 1
  fi
  echo "object-storage: setting up user $user for $buckets"
  shell "s3.configure -user $user -access_key $access_key -secret_key $secret_key -buckets $buckets -actions Read,Write,List,Tagging -apply" > /dev/null
done < /tmp/users

touch /tmp/ready
echo "object-storage: ready"
wait "$server_pid"
