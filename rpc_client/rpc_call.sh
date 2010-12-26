#/bin/bash

METHOD_NAME=$1
shift

DATA="<methodCall>"
DATA=$DATA"<methodName>$METHOD_NAME</methodName>"
DATA=$DATA"<params>"

for ARG in $@
do
    DATA=$DATA"<param><value><string>$ARG</string></value></param>"
done

DATA=$DATA"</params></methodCall>"

HOST="http://localhost:46212/RPC2"

curl --data "$DATA" $HOST
