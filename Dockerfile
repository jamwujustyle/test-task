FROM python:3.11.10

WORKDIR /project
COPY requirements.txt /project/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /project/


CMD ["python", "index.py"]