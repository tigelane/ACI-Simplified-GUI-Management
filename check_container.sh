#!/bin/bash

if docker inspect -f '{{.State.Running}}' $1
then
  echo Stopping the container
  docker stop $1
else
  echo No need to stop the container
fi