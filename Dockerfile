FROM python:3.11-slim

WORKDIR /work
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["neorepro"]
CMD ["status"]

