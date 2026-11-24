import { Alert, Card, Col, List, Row, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  loadKnowledgeHome,
  type KnowledgeConversation,
  type KnowledgeHome,
} from "../api/knowledge";

export function KnowledgeDashboard() {
  const navigate = useNavigate();
  const [home, setHome] = useState<KnowledgeHome | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadKnowledgeHome()
      .then((result) => {
        setHome(result);
        setError(null);
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Knowledge spaces could not be loaded");
      });
  }, []);

  if (error) {
    return <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} />;
  }
  if (!home) {
    return <Card loading style={{ marginBottom: 16 }} />;
  }

  return (
    <div style={{ marginBottom: 24 }}>
      <Typography.Title level={3} style={{ marginTop: 0 }}>
        Knowledge spaces
      </Typography.Title>
      <Typography.Paragraph>
        Choose a space for the kind of file you want to read and talk about. Each space keeps its
        own uploads and chats.
      </Typography.Paragraph>
      <Row gutter={[16, 16]}>
        {home.spaces.map((space) => (
          <Col xs={24} md={12} xl={8} key={space.id}>
            <Card
              title={space.label}
              extra={<Link to={`/knowledge/${space.id}`}>Open</Link>}
            >
              <Typography.Paragraph>{space.summary}</Typography.Paragraph>
              <Tag>{uploadLabel(space.document_count)}</Tag>
              <Tag>{chatLabel(space.conversation_count)}</Tag>
            </Card>
          </Col>
        ))}
      </Row>
      <Card title="Conversation history" style={{ marginTop: 16 }}>
        <List
          dataSource={home.conversations}
          locale={{ emptyText: "No chats yet. Open a space and ask about a file." }}
          renderItem={(item) => (
            <List.Item
              style={{ cursor: "pointer" }}
              onClick={() => navigate(destination(item))}
            >
              <List.Item.Meta
                title={item.title}
                description={item.filename ?? "No file attached"}
              />
              <Tag>{item.space_label}</Tag>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
}

function destination(item: KnowledgeConversation): string {
  if (!item.space || !item.document_id) {
    return `/assistant?conversation=${encodeURIComponent(item.id)}`;
  }
  const documentId = encodeURIComponent(item.document_id);
  const conversationId = encodeURIComponent(item.id);
  return `/knowledge/${item.space}?document=${documentId}&conversation=${conversationId}`;
}

function uploadLabel(count: number): string {
  return count === 1 ? "1 upload" : `${count} uploads`;
}

function chatLabel(count: number): string {
  return count === 1 ? "1 chat" : `${count} chats`;
}
