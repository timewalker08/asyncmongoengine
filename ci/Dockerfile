FROM python:3.8
USER root

WORKDIR /app
ENV PYTHONPATH=/app

CMD ["/bin/bash","-c","cd / && pip install --exists-action w -r /app/requirements.txt && echo Done && while true ; do sleep 3600; done"]