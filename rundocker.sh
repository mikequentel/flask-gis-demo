#!/bin/bash
export DOCKTAG=flask-gis-demo
export DOCKIMG=`docker images -q ${DOCKTAG}`
if [ -z "${DOCKIMG}" ]; then
  docker rm ${DOCKTAG}
  docker build -t ${DOCKTAG} .
fi
docker run --net="host" -p 8888:80 ${DOCKTAG}
# runs in detached mode
# docker run --net="host" -d -p 8888:80 ${DOCKTAG}
