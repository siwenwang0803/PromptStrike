{{/*
Expand the name of the chart.
*/}}
{{- define "promptstrike-sidecar.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "promptstrike-sidecar.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "promptstrike-sidecar.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "promptstrike-sidecar.labels" -}}
helm.sh/chart: {{ include "promptstrike-sidecar.chart" . }}
{{ include "promptstrike-sidecar.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: promptstrike
app.kubernetes.io/component: guardrail-sidecar
{{- end }}

{{/*
Selector labels
*/}}
{{- define "promptstrike-sidecar.selectorLabels" -}}
app.kubernetes.io/name: {{ include "promptstrike-sidecar.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "promptstrike-sidecar.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "promptstrike-sidecar.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the namespace to use
*/}}
{{- define "promptstrike-sidecar.namespaceName" -}}
{{- if .Values.namespace.create }}
{{- .Values.namespace.name }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}

{{/*
OPA Gatekeeper labels
*/}}
{{- define "promptstrike-sidecar.opaLabels" -}}
{{- if .Values.opa.enabled }}
gatekeeper.sh/operation: mutate
gatekeeper.sh/mutation: enabled
admission.gatekeeper.sh/ignore: "false"
{{- end }}
{{- end }}

{{/*
Security labels
*/}}
{{- define "promptstrike-sidecar.securityLabels" -}}
security-policy: restricted
pod-security.kubernetes.io/enforce: restricted
pod-security.kubernetes.io/audit: restricted
pod-security.kubernetes.io/warn: restricted
{{- end }}

{{/*
Common security annotations
*/}}
{{- define "promptstrike-sidecar.commonSecurityAnnotations" -}}
pod-security.kubernetes.io/enforce: "restricted"
pod-security.kubernetes.io/audit: "restricted"
pod-security.kubernetes.io/warn: "restricted"
{{- end }}

{{/*
Common security context
*/}}
{{- define "promptstrike-sidecar.securityContext" -}}
runAsUser: 65534
runAsGroup: 65534
runAsNonRoot: true
fsGroup: 65534
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
Container security context
*/}}
{{- define "promptstrike-sidecar.containerSecurityContext" -}}
runAsUser: 65534
runAsGroup: 65534
runAsNonRoot: true
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop:
  - ALL
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
Resource labels for monitoring
*/}}
{{- define "promptstrike-sidecar.monitoringLabels" -}}
{{- if .Values.monitoring.enabled }}
monitoring: enabled
prometheus.io/scrape: "true"
{{- end }}
{{- end }}