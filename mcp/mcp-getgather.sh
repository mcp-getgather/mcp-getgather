#! /bin/bash

DOCKER_MCP_URL=http://127.0.0.1:8000/mcp # change to your actual docker mcp url
HOST_URL_FOLDER=~/.cache/getgather
HOST_URL_FILE=$HOST_URL_FOLDER/url

open_browser() {
    mkdir -p $HOST_URL_FOLDER
    while true; 
    do 
        if [ -f $HOST_URL_FILE ]; then
            url=$(cat $HOST_URL_FILE 2> /dev/null)
            rm -f $HOST_URL_FILE
            if [[ "$OSTYPE" == "darwin"* ]]; then
                open "$url"
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                xdg-open "$url"
            elif [[ "$OSTYPE" == "cygwin" || "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                cmd.exe /C start "" "$url"
            else
                echo "Don't know how to open browser on this OS: $OSTYPE"
            fi
        fi
        sleep 0.5; 
    done 
}

start_mcp() {
    npx mcp-remote $DOCKER_MCP_URL 
}

open_browser & start_mcp 
