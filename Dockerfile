FROM python:3.9
#RUN mkdir -p /app/python
RUN mkdir /app

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
#COPY python/requirements.txt /app/python
COPY . /app

RUN pip3 install -r /app/python/requirements.txt
#COPY python /app
WORKDIR /app/python
CMD python3 main.py --kubeconfig '/app/python/kube_config' --address ":8080"
EXPOSE 5000

