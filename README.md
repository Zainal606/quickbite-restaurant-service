# QuickBite Restaurant Service

Owns restaurants and their menus. Other services read menu data only through this API.

Python 3.12, FastAPI, SQLAlchemy, PostgreSQL (SQLite for local development).

## API

| Type | Method | Path | Purpose |
|---|---|---|---|
| Command | POST | /restaurants | Register a restaurant |
| Command | PATCH | /restaurants/{id}/status | Open or close a restaurant |
| Command | POST | /restaurants/{id}/menu-items | Add a menu item |
| Command | PATCH | /menu-items/{id} | Change price or availability |
| Command | DELETE | /menu-items/{id} | Remove a menu item |
| Query | GET | /restaurants?city=&cuisine= | Browse restaurants |
| Query | GET | /restaurants/{id} | Restaurant with its menu |
| Query | GET | /restaurants/{id}/menu | Menu of a restaurant |
| Query | GET | /menu-items/{id} | One menu item |
| Ops | GET | /health | Health check, shows the pod that answered |

Interactive docs: `http://localhost:8001/docs`

## Project structure

```
restaurant-service/
├── app/
│   ├── main.py          # routes (commands and queries)
│   ├── models.py        # database tables
│   ├── schemas.py       # request and response models
│   └── database.py      # engine, session, startup retry
├── tests/               # pytest suite
├── k8s/
│   ├── namespace.yaml
│   ├── postgres.yaml    # this service's own database
│   └── deployment.yaml  # Deployment (2 replicas) + NodePort Service
├── Dockerfile
└── requirements.txt
```

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --port 8001
```

## Build the image

```bash
docker build -t quickbite/restaurant-service:1.0 .
```

## Deploy to minikube

```bash
minikube image load quickbite/restaurant-service:1.0
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/deployment.yaml
kubectl -n quickbite rollout status deployment/restaurant-service
minikube service restaurant-service -n quickbite --url
```

The service is exposed on NodePort 30081.
