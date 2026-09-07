FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# The whole context: the app, the templates and icons, and VERSION when the
# launcher or prepare-context.sh has staged it here (see .dockerignore for
# what stays out).
COPY . ./
ENV PYTHONUNBUFFERED=1
EXPOSE 7789
CMD ["gunicorn", "--bind", "0.0.0.0:7789", "--workers", "2", "--threads", "4", "app:app"]
