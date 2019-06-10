FROM jfloff/alpine-python:3.6-onbuild 
COPY requirements.txt /tmp 
WORKDIR /tmp 
<<<<<<< HEAD
RUN pip install -r requirements.txt 
WORKDIR /.
ADD watering_rules.py /
=======
RUN apk add --update tzdata
ENV TZ=Australia/Melbourne
RUN pip install --upgrade pip
RUN pip install -r requirements.txt 
WORKDIR /.
COPY . /
>>>>>>> v2.0
CMD [ "python", "./watering_rules.py" ]