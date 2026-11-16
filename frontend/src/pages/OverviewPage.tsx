import { Card, Col, Row, Tag, Typography } from "antd";
import { useEffect, useState } from "react";

import { loadServiceChecks, type ServiceCheck } from "../api/health";

const tagColor: Record<ServiceCheck["state"], string> = {
  up: "success",
  down: "error",
  unknown: "default",
};

export function OverviewPage() {
  const [checks, setChecks] = useState<ServiceCheck[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    loadServiceChecks()
      .then((result) => {
        if (active) {
          setChecks(result);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div>
      <Typography.Title level={3}>Platform overview</Typography.Title>
      <Typography.Paragraph>
        This is the foundation milestone. The API, PostgreSQL with pgvector, and this dashboard run
        together. Authentication, documents, retrieval, and agents are not available yet.
      </Typography.Paragraph>
      <Row gutter={[16, 16]}>
        {(loading ? placeholderChecks : checks).map((check) => (
          <Col xs={24} md={12} key={check.name}>
            <Card title={check.name} loading={loading}>
              <Tag color={tagColor[check.state]}>{check.state}</Tag>
              <Typography.Paragraph style={{ marginTop: 12, marginBottom: 0 }}>
                {check.detail}
              </Typography.Paragraph>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}

const placeholderChecks: ServiceCheck[] = [
  { name: "API", state: "unknown", detail: "Checking" },
  { name: "PostgreSQL", state: "unknown", detail: "Checking" },
];
