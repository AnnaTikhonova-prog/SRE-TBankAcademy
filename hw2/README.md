# ShiftPlanner в minikube — инструкция по развёртыванию

Развёртывание учебного приложения ShiftPlanner (React + FastAPI +
PostgreSQL) в однонодовом Kubernetes-кластере minikube.
Команды приведены для Windows PowerShell; пути — из корня проекта
(папки с `backend/`, `frontend/`, `k8s/`).

## 1. Требования

- Docker Desktop (запущен);
- minikube: `winget install Kubernetes.minikube`;
- kubectl: `winget install Kubernetes.kubectl`.

## 2. Запуск minikube

```powershell
minikube start --driver=docker
minikube status
```

## 3. Сборка образов (в docker-демоне minikube)

```powershell
# Аналог eval $(minikube docker-env) для PowerShell:
minikube docker-env --shell powershell | Invoke-Expression

docker build -t shiftplanner-backend:1.0 ./backend
docker build -t shiftplanner-frontend:1.0 ./frontend
```

## 4. Загрузка образов в minikube

```powershell
minikube image load shiftplanner-backend:1.0
minikube image load shiftplanner-frontend:1.0
```

## 5. Развёртывание

```powershell
kubectl apply -f ./k8s/
kubectl get pods -n shiftplanner -w     # ждём Running у всех подов
kubectl get all -n shiftplanner
```

## 6. Масштабирование

```powershell
kubectl scale deployment backend -n shiftplanner --replicas=3
kubectl get pods -n shiftplanner
```

## 7. Доступ к приложению

```powershell
minikube service frontend -n shiftplanner
```

(откроет браузер; если драйвер docker не пробрасывает NodePort напрямую,
используйте `kubectl port-forward svc/frontend 8080:80 -n shiftplanner`
и откройте http://localhost:8080)

Демо-аккаунты:

| Роль | Email | Пароль |
|---|---|---|
| Менеджер | `manager@example.com` | `manager123` |
| Сотрудник | `ivan@example.com` | `employee123` |

## 8. Очистка

```powershell
kubectl delete namespace shiftplanner   # удалить только приложение
minikube delete                          # удалить весь кластер
```

## Структура манифестов

| Файл | Содержимое |
|---|---|
| `k8s/00-namespace.yaml` | Namespace `shiftplanner` |
| `k8s/01-config.yaml` | ConfigMap с несекретной конфигурацией |
| `k8s/02-secret.yaml` | Secret: пароль БД, JWT-ключ |
| `k8s/03-postgres-initdb.yaml` | ConfigMap со схемой БД и демо-данными |
| `k8s/04-postgres.yaml` | PVC + Deployment + Service PostgreSQL |
| `k8s/05-backend.yaml` | Deployment + Service бэкенда |
| `k8s/06-frontend.yaml` | Deployment + Service (NodePort) фронтенда |
