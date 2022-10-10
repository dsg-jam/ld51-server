FROM alpine:3 as builder

COPY deploy/container/builder-repositories /etc/apk/repositories

RUN apk add --no-cache \
    poetry

WORKDIR /workspace/
COPY poetry.lock pyproject.toml README.md /workspace/
COPY ld51_server /workspace/ld51_server/

RUN poetry install
RUN rm -rf /workspace/dist
RUN poetry build -f wheel


FROM alpine:3

EXPOSE 80

RUN apk add --no-cache \
    py3-pip

RUN pip install \
    uvicorn[standard]

COPY --from=builder /workspace/dist/*.whl /tmp/ld51_server/
RUN pip install /tmp/ld51_server/*.whl && rm -rf /tmp/ld51_server/

COPY deploy/container/run.sh /run.sh

CMD ["/run.sh"]
