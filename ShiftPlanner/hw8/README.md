# HW8 — релизы и стратегии доставки трафика
 Бэкенд сохраняет состояние в общей PostgreSQL, возвращает версию в `/version` и заголовках `X-App-Version` / `X-App-Release`. Два release deployment (`backend-v1`, `backend-v2`) можно обслуживать независимо, а Envoy Gateway направляет к ним запросы через Gateway API.

## Что в каталоге

- `k8s/backends.yaml` — две версии бэкенда, по две реплики каждая, с readiness и liveness probes.
- `k8s/gateway.yaml` — GatewayClass, Gateway и начальный HTTPRoute.
- `routes/` — сменяемые HTTPRoute для blue/green, canary, A/B и shadow.
- `scripts/demo.ps1` — сборка/загрузка версий и воспроизводимые прогоны с записью ответов и логов в `artifacts/`.
- `Отчёт.md` — описание решений и таблица для ссылок на видео/логи каждой стратегии.

## Требования

PowerShell 7 или Windows PowerShell 5.1, Docker Desktop с Linux containers, `minikube`, `kubectl`, `helm`. Перед началом проверьте, что в namespace `shiftplanner` уже есть `shiftplanner-config`, `shiftplanner-secret` и Service `postgres` из основной установки. Если minikube остановлен, запустите Docker Desktop и выполните:

```powershell
minikube start
kubectl get pods -n shiftplanner
```

Для установки Envoy Gateway используется официальный Helm chart Envoy Gateway v1.7.5, который устанавливает необходимые Gateway API CRD. После установки создаются GatewayClass/Gateway и маршруты из этого каталога.

## Подготовка стенда

Из корня репозитория, в одном PowerShell:

```powershell
helm upgrade --install eg oci://docker.io/envoyproxy/gateway-helm --version v1.7.5 --namespace envoy-gateway-system --create-namespace
kubectl wait --timeout=5m -n envoy-gateway-system deployment/envoy-gateway --for=condition=Available
docker build -f .\ShiftPlanner\backend\Dockerfile --build-arg APP_VERSION=1.0.0 --build-arg APP_RELEASE=v1 -t shiftplanner-backend:1.0.0 .\ShiftPlanner\backend
docker build -f .\ShiftPlanner\backend\Dockerfile --build-arg APP_VERSION=2.0.0 --build-arg APP_RELEASE=v2 -t shiftplanner-backend:2.0.0 .\ShiftPlanner\backend
minikube image load shiftplanner-backend:1.0.0
minikube image load shiftplanner-backend:2.0.0
kubectl apply -f .\ShiftPlanner\hw8\k8s\backends.yaml
kubectl apply -f .\ShiftPlanner\hw8\k8s\gateway.yaml
kubectl rollout status deployment/backend-v1 -n shiftplanner
kubectl rollout status deployment/backend-v2 -n shiftplanner
kubectl get pods,svc,gateway,httproute -n shiftplanner
```

Сборка выполняется в обычном Docker Desktop, после неё образы загружаются в minikube командой `minikube image load`. На Windows `minikube docker-env` с containerd работает экспериментально и для этого задания не используется.

Gateway создаёт LoadBalancer Service.
```powershell
$envoyService = kubectl get svc -n envoy-gateway-system -l gateway.envoyproxy.io/owning-gateway-name=shiftplanner-gateway -o jsonpath='{.items[0].metadata.name}'
$envoyService
kubectl port-forward -n envoy-gateway-system "svc/$envoyService" 8080:80
```


## Стратегии и откат

Rolling обновляет `backend` с тега `1.0.0` до `2.0.0` через `kubectl set image`; `maxUnavailable: 0` и readiness проверка не дают снять старые pod'ы, пока новые не готовы. Скрипт возвращает Deployment к v1 после демонстрации.

Blue/Green, Canary, A/B и Shadow переключаются редактированием одного HTTPRoute. Blue/Green переключает весь трафик одним применением YAML, откат — повторным применением `blue-v1.yaml`. Canary задаёт веса 90/10 → 50/50 → 0/100. A/B направляет запрос с `X-Experiment: beta` на v2, а запрос без заголовка — на v1. Shadow отдаёт клиентский ответ от v1 и зеркалирует запросы на v2; ответы v2 игнорируются Gateway.

Gateway API использует относительные веса backendRefs, а `RequestMirror` — расширенный поддерживаемый Envoy Gateway фильтр. Источники: [официальная установка Envoy Gateway](https://gateway.envoyproxy.io/v1.7/install/install-helm/), [traffic splitting в Gateway API](https://gateway-api.sigs.k8s.io/guides/user-guides/traffic-splitting/), [request mirroring в Envoy Gateway](https://gateway.envoyproxy.io/latest/tasks/traffic/http-request-mirroring/).
