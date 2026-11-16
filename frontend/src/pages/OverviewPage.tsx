import { Card, Col, Row, Tag, Typography } from "antd";
import { useEffect, useState } from "react";

import { loadServiceChecks, type ServiceCheck } from "../api/health";
import { WorldBankPanel } from "./WorldBankPanel";

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
        Public World Bank indicators are charted here. Olist sales, reviews, and delivery from the
        2016–2018 Kaggle snapshot are on Analytics.
      </Typography.Paragraph>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
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
      <WorldBankPanel />
    </div>
  );
}

const placeholderChecks: ServiceCheck[] = [
  { name: "API", state: "unknown", detail: "Checking" },
  { name: "PostgreSQL", state: "unknown", detail: "Checking" },
];
