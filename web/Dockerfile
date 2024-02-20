FROM python:3.9

RUN apt-get update && apt-get install -y libpq-dev gcc
# need gcc to compile psycopg2

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && python -m pip install -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh wait-for-it.sh

ENTRYPOINT ["/entrypoint.sh"]
