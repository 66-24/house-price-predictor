FROM python:3.10-slim

ARG SOURCE_DATE_EPOCH
ARG BUILD_DATE
ARG AUTHOR
ARG VERSION
ARG GIT_SHA_SHORT
ARG TEAM

LABEL org.opencontainers.image.title="House Price Predictor UI" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$GIT_SHA_SHORT \
      org.opencontainers.image.authors=$AUTHOR \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.team=$TEAM

WORKDIR /app

COPY app.py requirements.txt ./

RUN pip install -r /app/requirements.txt

EXPOSE 8501

#Fixed execution cannot pass args. Can be overridden with --entrypoint
#ENTRYPOINT ["top", "-b"]

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]