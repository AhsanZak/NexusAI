import { ReloadOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Col, Row, Space, Tag, Typography } from "antd";
import { useCallback, useEffect, useState } from "react";

import { loadProviderStatus, type ProviderCheck, type ProviderReport } from "../api/debug";

export function ModelRouteBar({ compact = false }: { compact?: boolean }) {
  const [report, setReport] = useState<ProviderReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setReport(await loadProviderStatus());
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Provider status is unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <div>
      <Space align="center" wrap style={{ width: "100%", justifyContent: "space-between" }}>
        <div>
          <Typography.Text strong>
            Chat is using {report?.active_label ?? "an unknown model route"}
          </Typography.Text>
          {report ? (
            <Typography.Text type="secondary"> — {report.model || "no model selected"}</Typography.Text>
          ) : null}
        </div>
        <Button icon={<ReloadOutlined />} onClick={() => void refresh()} loading={loading}>
          Refresh
        </Button>
      </Space>
      {error ? <Alert type="error" showIcon message={error} style={{ marginTop: 12 }} /> : null}
      {compact ? (
        <Space wrap style={{ marginTop: 8 }}>
          {(report?.providers ?? []).map((item) => (
            <StatusTag key={item.id} item={item} named />
          ))}
        </Space>
      ) : (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          {(report?.providers ?? []).map((item) => (
            <Col xs={24} md={8} key={item.id}>
              <Card size="small">
                <Space direction="vertical" size={8} style={{ width: "100%" }}>
                  <Typography.Text strong>{item.name}</Typography.Text>
                  <StatusTag item={item} />
                  <Typography.Text type="secondary">{item.detail}</Typography.Text>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
}

function StatusTag({ item, named = false }: { item: ProviderCheck; named?: boolean }) {
  const color = item.state === "up" ? "success" : "error";
  const label = item.state === "up" ? "Working" : "Not working";
  return (
    <Tag color={color}>
      {named ? `${item.name}: ` : ""}
      {label}
      {item.active ? " · in use" : ""}
    </Tag>
  );
}
