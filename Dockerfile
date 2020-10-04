FROM ubuntu:18.04
RUN apt-get update && apt-get install --yes python3-poppler-qt5
RUN apt-get update && apt-get install --yes python3-pip
RUN python3 -m pip install pdftitle
RUN python3 -m pip install loguru
RUN python3 -m pip install arxiv
RUN mkdir /opt/paperutil
COPY main.py /opt/paperutil/main.py
# See https://chase-seibert.github.io/blog/2014/01/12/python-unicode-console-output.html
ENV PYTHONIOENCODING=UTF-8
CMD python3 /opt/paperutil/main.py