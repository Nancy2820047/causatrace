FROM python:3.12-slim
WORKDIR /app
COPY app/ app/
COPY scripts/ scripts/
COPY data/demo/ data/demo/
USER 65532:65532
EXPOSE 8000
CMD ["python", "-B", "-m", "scripts.serve_demo", "--host", "0.0.0.0"]
