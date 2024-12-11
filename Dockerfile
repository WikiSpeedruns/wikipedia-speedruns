FROM python:3.12-slim

WORKDIR /app
COPY . /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN apt-get update
RUN apt-get install -y nodejs npm

RUN npm install
EXPOSE 5000

ENV FLASK_ENV=development
ENV FLASK_APP=app

# CMD ["flask", "--app", "app", "run", "--debug", "--host", "0.0.0.0"]
CMD ["sh", "-c", "npm start & flask --app app run --debug --host 0.0.0.0"]