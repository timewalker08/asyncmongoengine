FROM python:3.9.16-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENV PYTHONPATH=/app

CMD ["/bin/bash","-c","echo READY... && while true ; do sleep 3600; done"]