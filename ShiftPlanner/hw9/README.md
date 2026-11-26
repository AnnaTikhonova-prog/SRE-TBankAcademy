# HW9 — Gateway API traffic split 90/10

Задание разворачивает две версии ShiftPlanner backend за Envoy Gateway. `GET /version` и response headers `X-App-Version` / `X-App-Release` позволяют определить, какой backend ответил на запрос.

## Состав

- `k8s/backend-versions.yaml` — Deployments `backend-v1`, `backend-v2` и их ClusterIP Services.
- `k8s/gateway-90-10.yaml` — GatewayClass, Gateway и HTTPRoute с весами 90/10.
- `scripts/measure.ps1` — отправка 200 запросов, подсчёт версий и сохранение CSV и access logs.
- `artifacts/` — фактический результат прогона.
- `Отчёт.md` — описания, манифесты, наблюдаемые числа и вывод.

В проверочном прогоне от 26.11.2026 отправлено 200 запросов: 179 ответов v1 и 21 ответ v2 (89,5%/10,5%). Полные CSV, HTTPRoute, backend logs и снимок состояния workload приложены в папке `artifacts/`.

## Запуск на Windows PowerShell

Предполагается, что основной ShiftPlanner уже развёрнут в namespace `shiftplanner` и там доступны ConfigMap/Secret и PostgreSQL Service/PVC. Docker Desktop должен работать.

Из корня репозитория:

```powershell
minikube start
helm upgrade --install eg oci://docker.io/envoyproxy/gateway-helm --version v1.7.5 --namespace envoy-gateway-system --create-namespace
kubectl wait --timeout=5m -n envoy-gateway-system deployment/envoy-gateway --for=condition=Available
docker build -f .\ShiftPlanner\backend\Dockerfile --build-arg APP_VERSION=1.0.0 --build-arg APP_RELEASE=v1 -t shiftplanner-backend:1.0.0 .\ShiftPlanner\backend
docker build -f .\ShiftPlanner\backend\Dockerfile --build-arg APP_VERSION=2.0.0 --build-arg APP_RELEASE=v2 -t shiftplanner-backend:2.0.0 .\ShiftPlanner\backend
minikube image load shiftplanner-backend:1.0.0
minikube image load shiftplanner-backend:2.0.0
kubectl apply -f .\ShiftPlanner\hw9\k8s\backend-versions.yaml
kubectl apply -f .\ShiftPlanner\hw9\k8s\gateway-90-10.yaml
kubectl rollout status deployment/backend-v1 -n shiftplanner
kubectl rollout status deployment/backend-v2 -n shiftplanner
```

Перед тестом Gateway и backend Services должны быть готовы. Откройте отдельный PowerShell и оставьте port-forward работающим:

```powershell
$envoyService = kubectl get svc -n envoy-gateway-system -l gateway.envoyproxy.io/owning-gateway-name=shiftplanner-gateway -o jsonpath='{.items[0].metadata.name}'
kubectl port-forward -n envoy-gateway-system "svc/$envoyService" 8080:80
```

В другом PowerShell из корня проекта:

```powershell
.\ShiftPlanner\hw9\scripts\measure.ps1
```

По умолчанию скрипт отправляет 200 запросов, печатает числа и доли v1/v2 и складывает результаты в `ShiftPlanner/hw9/artifacts/`. Можно задать другое количество от 100 до 200: `.ShiftPlannerhw9scriptsmeasure.ps1 -Count 150`.

Планировщик Envoy выбирает backend по относительным весам, поэтому при конечной выборке фактические количества могут немного отличаться от точных 90/10. Оценивается доля около заданного соотношения.
