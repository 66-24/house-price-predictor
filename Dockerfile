FROM python:3.11-slim
# dataflow/house-price-predictor                   v1                 efcd9bcf0e95   45 years ago         815MB
# SOURCE_DATE_EPOCH fixes this
ARG SOURCE_DATE_EPOCH
ARG BUILD_DATE
LABEL org.opencontainers.image.created=$BUILD_DATE


WORKDIR /app

COPY src/api/requirements.txt .
# system to bypass venv
RUN pip install -r requirements.txt && \
    rm -rf /root/.cache/pip /usr/share/doc/* /usr/share/man/*

COPY src/api/ /app
COPY models/trained/ /app/models/trained/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
