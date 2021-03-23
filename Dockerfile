FROM python:3.8-buster

WORKDIR /script
RUN cd /script

COPY . .

RUN pip install pipenv
RUN pipenv install
CMD ["pipenv", "run", "python", "main.py"]
