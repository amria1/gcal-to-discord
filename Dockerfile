ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG UID=10001
RUN adduser \
--disabled-password \
--gecos "" \
--home "/nonexistent" \
--shell "/sbin/nologin" \
--no-create-home \
--uid "${UID}" \
appuser

RUN --mount=type=cache,target=/root/.cache/pip \
--mount=type=bind,source=requirements.txt,target=requirements.txt \
python -m pip install -r requirements.txt

USER appuser
WORKDIR /app
COPY . .
CMD ["python", "main.py"]

