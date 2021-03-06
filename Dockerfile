FROM ubuntu:16.04
MAINTAINER Matt Borgerson version:0.1

# Install required packages
RUN apt-get update && apt-get install -y build-essential libtool-bin wget python automake autoconf bison libglib2.0-dev libc6-dev-i386 valgrind

# Copy files over to container
COPY . /app
RUN ln -s /app/fuzz /fuzz
