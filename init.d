#!/bin/sh -e

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

### BEGIN INIT INFO
# Provides:          kts46
# Required-Start:    $local_fs $remote_fs
# Required-Stop:     $local_fs $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: kts46 init script
# Description:       kts46 init script for servers.
### END INIT INFO

SCRIPT_OK=0
SCRIPT_ERROR=1

DESCRIPTION="kts46 servers"
NAME=couchdb
SCRIPT_NAME=`basename $0`
SCHEDULER="python /anthony/Desktop/kts46/rpc_server/scheduler.py 2> /dev/null &"
RPC_SERVER="python /anthony/Desktop/kts46/rpc_server/rpc_server.py 2> /dev/null &"
WORKER="python /anthony/Desktop/kts46/rpc_server/worker.py 2> /dev/null &"
# RUN_DIR=/var/run/couchdb
LSB_LIBRARY=/lib/lsb/init-functions

# Grace time in seconds to give the beam process to stop when we're running the
# stop target. Will end before grace time ends if the process ends sooner.
STOP_GRACE_TIME=5

log_daemon_msg () {
    # Dummy function to be replaced by LSB library.

    echo $@
}

log_end_msg () {
    # Dummy function to be replaced by LSB library.

    if test "$1" != "0"; then
      echo "Error with $DESCRIPTION: $NAME"
    fi
    return $1
}

if test -r $LSB_LIBRARY; then
    . $LSB_LIBRARY
fi


start_kts46 () {
    $SCHEDULER
    $RPC_SERVER
    $WORKER
    return $SCRIPT_OK
}

stop_couchdb () {
    # Stop the running Apache CouchDB process.

    pidFile="$RUN_DIR/couchdb.pid"
    if [ ! -r "$pidFile" ]
    then
        #exists, but can't read it
        [ -f "$pidFile" ] && return $SCRIPT_ERROR

        #doesn't exist, so assume couchdb is already stopped
        return $SCRIPT_OK
    fi

    pid=`cat $pidFile`
    #unset $pidFile
    [ -z "$pid" ] && return $SCRIPT_OK

    command="$COUCHDB -d"
    if test -n "$COUCHDB_OPTIONS"; then
        command="$command $COUCHDB_OPTIONS"
    fi

    # We need `heart`'s pid because its ppid is set to 1 when the beam proc
    # ends, thereby hiding itself from our `ps` check bellow.
    heart_pid=`ps -f --ppid $pid | grep "heart -pid $pid " | awk '{print $2}'`
    [ -n "$heart_pid" ] && heart_pid=",$heart_pid" #for `ps` call formatting

    if test -n "$COUCHDB_USER"; then
        if ! su $COUCHDB_USER -c "$command" > /dev/null; then
            return $SCRIPT_ERROR
        fi
    else
        if ! $command > /dev/null; then
            return $SCRIPT_ERROR
        fi
    fi

    i=0
    while ps -p $pid$heart_pid --ppid $pid$heart_pid > /dev/null
    do
        [ $i -ge $STOP_GRACE_TIME ] && return $SCRIPT_ERROR

        sleep 1
        i=`expr $i + 1`
    done

    return $SCRIPT_OK
}

parse_script_option_list () {
    # Parse arguments passed to the script and take appropriate action.

    case "$1" in
        start)
            log_daemon_msg "Starting $DESCRIPTION" $NAME
            if start_kts46; then
                log_end_msg $SCRIPT_OK
            else
                log_end_msg $SCRIPT_ERROR
            fi
            ;;
        stop)
            log_daemon_msg "Stopping $DESCRIPTION" $NAME
            if stop_kts46; then
                log_end_msg $SCRIPT_OK
            else
                log_end_msg $SCRIPT_ERROR
            fi
            ;;
        restart|force-reload)
            log_daemon_msg "Restarting $DESCRIPTION" $NAME
            if stop_kts46; then
                if start_kts46; then
                    log_end_msg $SCRIPT_OK
                else
                    log_end_msg $SCRIPT_ERROR
                fi
            else
                log_end_msg $SCRIPT_ERROR
            fi
            ;;
        *)
            cat << EOF >&2
Usage: $SCRIPT_NAME {start|stop|restart|force-reload}
EOF
            exit $SCRIPT_ERROR
            ;;
    esac
}

parse_script_option_list $@
