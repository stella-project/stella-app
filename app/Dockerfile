FROM python:3.7

RUN apt-get update && apt-get install -y libpq-dev gcc
# need gcc to compile psycopg2
RUN pip3 install psycopg2~=2.6
RUN apt-get autoremove -y gcc

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["stella-app.py"]