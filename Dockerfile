FROM ubuntu:18.04
RUN apt-get update && apt-get install --yes python3-poppler-qt5
RUN mkdir /opt/paperutil
COPY main.py /opt/paperutil/main.py
CMD python3 /opt/paperutil/main.py