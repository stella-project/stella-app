FROM python:3.9

ENV TZ=Europe/Berlin  

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && python -m pip install -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh wait-for-it.sh

ENTRYPOINT ["/entrypoint.sh"]
