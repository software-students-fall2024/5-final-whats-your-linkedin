FROM python:3.9-slim-buster

WORKDIR /webapp
# Copy requirements from the root directory 
COPY requirements.txt ./

RUN pip3 install --trusted-host pypi.python.org -r requirements.txt
COPY .env .env
ADD . .

EXPOSE 5000
CMD [ "python3", "-m", "flask", "run", "--host=0.0.0.0"]