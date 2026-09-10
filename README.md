GymBros

Aplicación móvil de entrenamiento personal. El deportista registra sus mediciones corporales, crea y ejecuta sus rutinas, y hace seguimiento de su progreso — sin depender de un gimnasio.

Proyecto de la materia Aplicaciones Móviles · MVC · Popayán, Colombia

Estructura del repositorio
GymBros/
├── gymbros-api/     Backend — FastAPI + PostgreSQL
├── gymbros-app/     App móvil — React Native (pendiente)
├── docs/            Requisitos, reglas de negocio, diccionario de datos y guías
└── docker-compose.yml
Arrancar el proyecto
powershell
docker compose up --build

Las instrucciones completas — incluido el modo con venv para quien no pueda usar Docker — están en el README del backend.

Qué	URL
API	http://localhost:8001
Swagger (documentación y pruebas)	http://localhost:8001/docs
