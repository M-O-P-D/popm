FROM python:3.8

WORKDIR /app

COPY . /app

# install non-python deps
RUN apt-get update -y && apt-get install --no-install-recommends -y libspatialindex-dev=1.9.0-1 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# ensure pip is up to date and install deps
RUN python -m pip install -U pip \
 && python -m pip install -r requirements.txt

# default mesa port
EXPOSE 8521

CMD ["mesa", "runserver", "."]