FROM jfloff/alpine-python:3.6-onbuild 
COPY requirements.txt /tmp 
WORKDIR /tmp 
RUN pip install -r requirements.txt 
WORKDIR /.
ADD watering_rules.py /
CMD [ "python", "./watering_rules.py" ]