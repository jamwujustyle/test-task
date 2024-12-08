FROM python

WORKDIR /project
COPY . /project

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python" "index.py"]