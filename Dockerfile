FROM pypy
RUN mkdir /app
COPY . /app
RUN python3