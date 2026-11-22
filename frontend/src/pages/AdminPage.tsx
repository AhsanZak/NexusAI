import { ReloadOutlined, TeamOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Col, Row, Space, Tag, Typography } from "antd";
import { useCallback, useEffect, useState } from "react";

import { loadAuthorizationDemo, type AccessDecision, type AuthzDemo } from "../api/authz";

export function AdminPage() {
  const [demo, setDemo] = useState<AuthzDemo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setDemo(await loadAuthorizationDemo());
      setError(null);
    } catch (reason) {
      setDemo(null);
      setError(reason instanceof Error ? reason.message : "OpenFGA is unavailable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const users = demo ? uniqueUsers(demo.decisions) : [];

  return (
    <div>
      <Space align="center" wrap style={{ width: "100%", justifyContent: "space-between" }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          <TeamOutlined /> OpenFGA access
        </Typography.Title>
        <Button icon={<ReloadOutlined />} onClick={() => void refresh()} loading={loading}>
          Recheck
        </Button>
      </Space>
      <Typography.Paragraph style={{ marginTop: 12 }}>
        Amina Rahman and Luis Ortega both may view the World Bank indicators. Amina alone may
        analyze the Olist sales warehouse. Luis alone may audit the finance review notes. OpenFGA
        Check makes each decision, and the text is returned only after an allow.
      </Typography.Paragraph>
      {error ? <Alert type="error" showIcon message="OpenFGA did not answer" description={error} /> : null}
      {demo ? (
        <Typography.Paragraph type="secondary">
          Store {demo.store_id} · model {demo.authorization_model_id} · {demo.api_url}
        </Typography.Paragraph>
      ) : null}
      <Row gutter={[16, 16]}>
        {users.map((user) => (
          <Col xs={24} lg={12} key={user.user_id}>
            <Card title={`${user.display_name} · ${user.role}`}>
              <Space direction="vertical" size={16} style={{ width: "100%" }}>
                {demo?.decisions
                  .filter((item) => item.user_id === user.user_id)
                  .map((item) => (
                    <DecisionRow key={`${item.user_id}-${item.object_id}`} item={item} />
                  ))}
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}

function DecisionRow({ item }: { item: AccessDecision }) {
  return (
    <div>
      <Space wrap>
        <Tag color={item.allowed ? "success" : "error"}>{item.allowed ? "Allowed" : "Denied"}</Tag>
        {item.shared ? <Tag color="blue">Shared</Tag> : null}
        {item.allowed && !item.shared ? <Tag>Only this user</Tag> : null}
        <Typography.Text strong>
          {item.relation} on {item.object_name}
        </Typography.Text>
      </Space>
      <Typography.Paragraph type={item.allowed ? undefined : "secondary"} style={{ marginTop: 8, marginBottom: 0 }}>
        {item.allowed ? item.content : "OpenFGA denied this document, so its text was not returned."}
      </Typography.Paragraph>
    </div>
  );
}

function uniqueUsers(decisions: AccessDecision[]): AccessDecision[] {
  const seen = new Set<string>();
  return decisions.filter((item) => {
    if (seen.has(item.user_id)) {
      return false;
    }
    seen.add(item.user_id);
    return true;
  });
}
