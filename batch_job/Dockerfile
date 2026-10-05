# 批处理任务镜像：tushare 财务报表拉取入库
FROM docker.m.daocloud.io/library/python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY fetch_financials.py .

CMD ["python", "fetch_financials.py"]
