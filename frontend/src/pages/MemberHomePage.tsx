import { ArrowRightOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Col, Row, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { loadMyAccess, type MyAccess } from "../api/access";
import { KnowledgeDashboard } from "../components/KnowledgeDashboard";

export function MemberHomePage() {
  const [access, setAccess] = useState<MyAccess | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadMyAccess()
      .then((result) => {
        setAccess(result);
        setError(null);
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Access could not be checked");
      });
  }, []);

  if (error) {
    return <Alert type="error" showIcon message={error} />;
  }
  if (!access) {
    return <Card loading />;
  }

  const actorLabel = access.actor === "super_admin" ? "super admin" : "member";

  return (
    <div>
      <Typography.Title level={3}>{access.display_name}</Typography.Title>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message={`Signed in as a ${actorLabel}`}
        description={`${access.email} is checked in OpenFGA as this account. A guest is a different subject and is not this login.`}
      />
      <KnowledgeDashboard />
      <Row gutter={[16, 16]}>
        {access.features.map((feature) => (
          <Col xs={24} md={12} key={feature.object_id}>
            <Card title={feature.name}>
              <Tag color={feature.allowed ? "success" : "error"}>{feature.allowed ? "Allowed" : "Denied"}</Tag>
              <Typography.Paragraph style={{ marginTop: 12 }}>
                {feature.object_id === "feature:ai-model"
                  ? "Questions go to the model only when this grant is allowed. Document text is still checked one document at a time."
                  : "The analysis page opens only when this grant is allowed."}
              </Typography.Paragraph>
              {feature.allowed ? (
                <Link to={feature.object_id === "feature:ai-model" ? "/assistant" : "/analytics"}>
                  <Button type="primary" icon={<ArrowRightOutlined />}>
                    Open
                  </Button>
                </Link>
              ) : null}
            </Card>
          </Col>
        ))}
      </Row>
      <Typography.Paragraph style={{ marginTop: 16 }}>
        <Link to="/documents">Open documents</Link> to see what this account can read, and what a guest can read.
      </Typography.Paragraph>
    </div>
  );
}
