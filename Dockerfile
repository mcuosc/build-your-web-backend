FROM python:3.9.18-alpine3.18

WORKDIR /app
COPY . .
# RUN pip3 install -r requirements.txt
RUN pip3 install pipenv
RUN pipenv install --system --deploy --ignore-pipfile
CMD ["pipenv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "443", "--ssl-keyfile", "privkey1.pem", "--ssl-certfile", "cert1.pem"]