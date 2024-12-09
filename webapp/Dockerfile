FROM python:3.9-slim-buster

WORKDIR /webapp
COPY requirements.txt ./

RUN pip3 install --trusted-host pypi.python.org -r requirements.txt
COPY .env .env

ADD . .

# expose the port that the Flask app is running on, by default 5000
EXPOSE 5000

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]