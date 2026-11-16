export interface HealthResponse {
  status: string;
  service: string;
}

export interface ReadinessResponse {
  status: string;
  database: string;
}

export interface ServiceCheck {
  name: string;
  state: "up" | "down" | "unknown";
  detail: string;
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function loadServiceChecks(): Promise<ServiceCheck[]> {
  const checks: ServiceCheck[] = [];

  try {
    const health = await readJson<HealthResponse>("/api/v1/health");
    checks.push({
      name: "API",
      state: health.status === "ok" ? "up" : "down",
      detail: health.service,
    });
  } catch (error) {
    checks.push({
      name: "API",
      state: "down",
      detail: error instanceof Error ? error.message : "API request failed",
    });
  }

  try {
    const readiness = await readJson<ReadinessResponse>("/api/v1/health/ready");
    checks.push({
      name: "PostgreSQL",
      state: readiness.database === "up" ? "up" : "down",
      detail: readiness.status,
    });
  } catch (error) {
    checks.push({
      name: "PostgreSQL",
      state: "down",
      detail: error instanceof Error ? error.message : "Readiness request failed",
    });
  }

  return checks;
}
