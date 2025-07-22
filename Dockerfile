# Creates the house-price-predictor-service image that wraps the model using FastAPI
FROM python:3.11-slim
# dataflow/house-price-predictor                   v1                 efcd9bcf0e95   45 years ago         815MB
# Created shows `45 years ago`;  SOURCE_DATE_EPOCH fixes this
ARG SOURCE_DATE_EPOCH
ARG BUILD_DATE
ARG AUTHOR
ARG VERSION
ARG GIT_SHA_SHORT
ARG TEAM
ARG IMAGE_NAME

LABEL org.opencontainers.image.title=$IMAGE_NAME \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$GIT_SHA_SHORT \
      org.opencontainers.image.authors=$AUTHOR \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.team=$TEAM

WORKDIR /app

COPY src/api/requirements.txt .
# system to bypass venv
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -rf /root/.cache/pip /usr/share/doc/* /usr/share/man/*

COPY src/api/ /app
COPY models/trained/ /app/models/trained/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
