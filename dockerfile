#Make wsgi.py before deploying
FROM python:3.13.2-bookworm
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "wsgi:app", "-b", "0.0.0.0:5000"]
