# pull base image
FROM dokken/ubuntu-21.04

RUN apt update
RUN apt install build-essential -y
RUN apt install libffi-dev -y
RUN apt install python3-dev -y
RUN apt install python3-pip -y
RUN apt install gcc -y
RUN apt install musl-dev -y	

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
