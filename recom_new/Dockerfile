FROM python:3.7

COPY ./script /script
COPY ./requirements.txt requirements.txt

RUN apt-get update && apt-get install -y python3
RUN pip install -r requirements.txt

WORKDIR /script

#CMD ["python", "recommand_dataset"]
CMD ["python3", "app.py"]
