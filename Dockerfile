# set base image (host OS)
FROM python:3.6

RUN python3.6 -m pip install --upgrade pip

# copy the content of the local src directory to the working directory
COPY . /app
WORKDIR /app

# install dependencies
RUN pip install -r requirements.txt

# command to run on container start
CMD [ "python", "-u", "runner.py" ]
