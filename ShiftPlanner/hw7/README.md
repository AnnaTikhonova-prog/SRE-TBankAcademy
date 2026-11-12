# Grafana dashboards for ShiftPlanner

This folder contains the Grafana deployment values, the exported ShiftPlanner dashboard, and a locally adapted copy of the community PostgreSQL Exporter dashboard (Grafana.com dashboard 9628).

## Deploy

Run from the repository root in PowerShell. The existing Minikube profile and the VictoriaMetrics Helm release `vm-single` are reused.

```powershell
minikube start
kubectl get pods -n shiftplanner
kubectl get pods -n monitoring
```

If VictoriaMetrics is not installed yet, deploy it using the course HW4 instructions in `ShiftPlanner\k8s\METRICS.md`. For a 30-day SLA window, upgrade its retention to 35 days:

```powershell
helm upgrade vm-single vm/victoria-metrics-single --namespace monitoring --reuse-values -f .\ShiftPlanner\hw7\victoria-metrics-retention-values.yaml
```

Add the Grafana chart and install it. The chart creates a random admin password in the Kubernetes Secret `grafana`:

```powershell
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo update
helm upgrade --install grafana grafana-community/grafana --namespace monitoring --create-namespace -f .\ShiftPlanner\hw7\grafana-values.yaml
```

Publish the two dashboard JSON files as ConfigMaps. The PostgreSQL dashboard is based on the community dashboard ID 9628 and uses the labels and VictoriaMetrics datasource UID in this project.

```powershell
kubectl create configmap shiftplanner-dashboard -n monitoring --from-file=shiftplanner.json=.\ShiftPlanner\hw7\dashboards\shiftplanner.json --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap shiftplanner-dashboard -n monitoring grafana_dashboard=1 --overwrite
kubectl create configmap postgres-exporter-dashboard -n monitoring --from-file=postgresql-database-9628.json=.\ShiftPlanner\hw7\dashboards\postgresql-database-9628.json --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap postgres-exporter-dashboard -n monitoring grafana_dashboard=1 --overwrite
```

Open Grafana from Windows PowerShell:

```powershell
kubectl port-forward svc/grafana 3000:80 -n monitoring
```

Browse to `http://localhost:3000`. The username is `admin`. To retrieve the generated password:

```powershell
$s = kubectl get secret grafana -n monitoring -o json | ConvertFrom-Json
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s.data.'admin-password'))
```

The dashboards are provisioned in the `ShiftPlanner` folder. The dashboard export for the application is `dashboards\shiftplanner.json`.

## Screenshots and recording

Store the required Grafana screenshots in `screenshots\` and the short screen recording here before packaging. Screenshots must show the actual loaded panels and the selected time range. Do not use example or fabricated screenshots.
