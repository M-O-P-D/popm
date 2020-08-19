FROM python:3.8

WORKDIR /app

COPY . /app

# install non-python deps
RUN apt-get update -y && apt-get install --no-install-recommends -y libspatialindex-dev

# install python deps
RUN python -m pip install -r requirements.txt

# default mesa port
EXPOSE 8521

CMD ["mesa", "runserver", "."]