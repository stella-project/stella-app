FROM python:3.7

COPY ./script /script
COPY ./requirements.txt requirements.txt

COPY . .

#RUN apt-get update && apt-get install -y python3
RUN pip install -r requirements.txt

#RUN python3 app.py
#WORKDIR /script

#CMD ["python", "recommand_dataset"]
CMD ["python3", "app.py"]
