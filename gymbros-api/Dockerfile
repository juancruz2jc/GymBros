# Alpine (musl) en vez de slim (glibc): ~186 MB en disco frente a ~304 MB.
# Todas las dependencias de requirements.txt publican wheels `musllinux`, así
# que pip no compila nada. Si una dependencia nueva no los trae y el build
# falla con `gcc: not found`, agregar antes del pip install:
#   RUN apk add --no-cache build-base libffi-dev postgresql-dev
# La imagen no trae bash: para entrar al contenedor usar `sh`.
FROM python:3.12-alpine

WORKDIR /code
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]