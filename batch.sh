#!/bin/bash
# usage: batch.sh <tag> name:kind:model ...   runs each 10-minute game consecutively, copies videos to ~/Downloads
cd ~/Github/nng-bench
TAG=$1; shift
for spec in "$@"; do
  IFS=: read name kind model <<<"$spec"
  ./run.sh "$name" "$kind" "$model" 600 2>/dev/null
  cp "runs/$name/screen.webm" "$HOME/Downloads/nng-$name.webm"
done
echo ALLDONE > runs/$TAG.done
