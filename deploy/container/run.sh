#!/usr/bin/env sh
exec uvicorn \
    --host "0.0.0.0" \
    --port "80" \
    ld51_server:app
