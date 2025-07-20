FROM python:3.10-slim

ARG SOURCE_DATE_EPOCH
LABEL authors="Srini"

WORKDIR /app

COPY app.py requirements.txt ./

RUN pip install -r /app/requirements.txt

EXPOSE 8501

#Fixed execution cannot pass args. Can be overridden with --entrypoint
#ENTRYPOINT ["top", "-b"]

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]