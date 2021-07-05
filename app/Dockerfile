FROM python:3.7

RUN apt-get update && apt-get install -y libpq-dev gcc
# need gcc to compile psycopg2

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["stella-app.py"]