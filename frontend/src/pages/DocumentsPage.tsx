import { ReloadOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Space, Tag, Typography } from "antd";
import { useCallback, useEffect, useState } from "react";

import { loadMyAccess, type MyAccess } from "../api/access";

export function DocumentsPage() {
  const [access, setAccess] = useState<MyAccess | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setAccess(await loadMyAccess());
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Access could not be checked");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (error) {
    return <Alert type="error" showIcon message={error} />;
  }
  if (!access) {
    return <Card loading />;
  }

  const actorLabel = access.actor === "super_admin" ? "super admin" : "member";

  return (
    <div>
      <Space className="page-heading" align="center" wrap>
        <Typography.Title level={3} style={{ margin: 0 }}>
          Documents for {access.display_name}
        </Typography.Title>
        <Button icon={<ReloadOutlined />} onClick={() => void refresh()} loading={loading}>
          Recheck
        </Button>
      </Space>
      <Typography.Paragraph style={{ marginTop: 12 }}>
        OpenFGA is checking this login as a {actorLabel}. Guest access is a separate check. The
        text below is returned only when this account is allowed. A guest allow does not reveal the
        text to a denied account.
      </Typography.Paragraph>
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        {access.documents.map((document) => (
          <Card key={document.object_id} title={document.object_name}>
            <Space wrap>
              <Tag color={document.allowed ? "success" : "error"}>
                {actorLabel}: {document.allowed ? "Allowed" : "Denied"}
              </Tag>
              <Tag color={document.guest_allowed ? "success" : "default"}>
                Guest: {document.guest_allowed ? "Allowed" : "Denied"}
              </Tag>
              <Typography.Text type="secondary">Requires {document.relation}</Typography.Text>
            </Space>
            <Typography.Paragraph style={{ marginTop: 12, marginBottom: 0 }}>
              {document.allowed
                ? document.content
                : "OpenFGA denied this document for the signed-in account, so its text was not returned."}
            </Typography.Paragraph>
          </Card>
        ))}
      </Space>
      <Card title="Grants for this account" style={{ marginTop: 16 }}>
        <GrantList assignments={access.assignments} empty="No grants for this account yet." />
      </Card>
      <Card title="Guest grants" style={{ marginTop: 16 }}>
        <GrantList assignments={access.guest_assignments} empty="A guest has no grants." />
      </Card>
    </div>
  );
}

function GrantList({
  assignments,
  empty,
}: {
  assignments: MyAccess["assignments"];
  empty: string;
}) {
  if (assignments.length === 0) {
    return <Typography.Text type="secondary">{empty}</Typography.Text>;
  }
  return (
    <Space direction="vertical">
      {assignments.map((item) => (
        <Typography.Text key={`${item.actor}-${item.object_id}-${item.relation}`}>
          {item.actor} · {item.relation} on {item.object_name}
        </Typography.Text>
      ))}
    </Space>
  );
}
