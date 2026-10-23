# VictoriaMetrics и метрики ShiftPlanner

В этом задании используется официальный Helm chart `vm/victoria-metrics-single`
(версия chart `0.49.0`) с включённым сбором по Kubernetes pod service discovery.
Grafana не устанавливается. Значения Helm находятся в
[`victoria-metrics-values.yaml`](victoria-metrics-values.yaml).

## Установка

Команды выполняются из корня репозитория в PowerShell. Перед установкой
VictoriaMetrics убедитесь, что существующие PostgreSQL и приложение работают:

Если Helm CLI ещё не установлен, в Windows его можно установить через WinGet:

```powershell
winget install Helm.Helm
```

```powershell
minikube status
docker build -t shiftplanner-backend:1.2 .\ShiftPlanner\backend
minikube image load shiftplanner-backend:1.2
kubectl apply -f .\ShiftPlanner\k8s\00-namespace.yaml
kubectl apply -f .\ShiftPlanner\k8s\01-config.yaml
# Перед запуском замените placeholder-значения в 02-secret.yaml своими.
kubectl apply -f .\ShiftPlanner\k8s\02-secret.yaml
kubectl apply -f .\ShiftPlanner\k8s\03-postgres-initdb.yaml
kubectl apply -f .\ShiftPlanner\k8s\04-postgres.yaml
kubectl rollout status deployment/postgres -n shiftplanner
kubectl apply -f .\ShiftPlanner\k8s\05-backend.yaml
kubectl rollout status deployment/backend -n shiftplanner
```

Добавьте VictoriaMetrics chart и установите single-node TSDB. vmagent скрейпинг
настроен в `server.scrape.config`; pod annotations выбирают только приложение и
PostgreSQL exporter.

```powershell
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo update
helm upgrade --install vm-single vm/victoria-metrics-single `
  --version 0.49.0 `
  --namespace monitoring --create-namespace `
  --values .\ShiftPlanner\k8s\victoria-metrics-values.yaml
kubectl get pods,svc,pvc -n monitoring
```

## Проверка метрик

```powershell
kubectl port-forward svc/vm-single-victoria-metrics-single-server -n monitoring 8428:8428
```

В другом окне PowerShell проверьте сырые метрики и запросы VictoriaMetrics:

```powershell
Invoke-WebRequest http://localhost:8428/api/v1/label/__name__/values | Select-Object -Expand Content
Invoke-WebRequest 'http://localhost:8428/api/v1/query?query=up' | Select-Object -Expand Content
Invoke-WebRequest 'http://localhost:8428/api/v1/query?query=shiftplanner_shifts_created_total' | Select-Object -Expand Content
Invoke-WebRequest 'http://localhost:8428/api/v1/query?query=pg_up' | Select-Object -Expand Content
```

`up` должен показывать успешно скрейпимые pod-таргеты; бизнес-счётчики появятся
после соответствующих действий пользователя. Для проверки самого endpoint
приложения:

```powershell
kubectl port-forward deployment/backend -n shiftplanner 8000:8000
Invoke-WebRequest http://localhost:8000/metrics | Select-Object -Expand Content
```

В `/metrics` доступны стандартные Python runtime метрики, HTTP request counter и
histogram, а также следующие бизнес-метрики:

| Метрика | Что считает |
| --- | --- |
| `shiftplanner_registered_users_total{role}` | Зарегистрированные аккаунты отдельно для менеджеров и сотрудников |
| `shiftplanner_auth_logins_total{result}` | Успешные и неуспешные попытки входа |
| `shiftplanner_companies_created_total` | Созданные компании |
| `shiftplanner_employees_joined_total` | Сотрудники, вступившие в компанию по invite-коду |
| `shiftplanner_shifts_created_total` | Успешно созданные рабочие смены |
| `shiftplanner_availability_blocks_created_total` | Добавленные интервалы доступности сотрудников |

PostgreSQL exporter работает sidecar-контейнером в pod PostgreSQL и отдаёт
метрики на `:9187/metrics`. Sidecar использует ту же сеть пода и секрет пароля
БД; Prometheus annotations находятся в шаблоне pod. У backend такие же
annotations указывают путь `/metrics` на порту `8000`.

## Демонстрация для скринкаста

Покажите в короткой записи следующие шаги и сохраните видео в
`ShiftPlanner/hw4/` перед упаковкой архива:

1. `kubectl get pods -n monitoring` и `kubectl get svc -n monitoring`.
2. `kubectl get pods -n shiftplanner`.
3. Доступность `/metrics` у приложения.
4. Ответы API-запросов VictoriaMetrics для `up`, `pg_up` и
   `shiftplanner_shifts_created_total`.

