import { ArrowRightOutlined, DeleteOutlined, FileExclamationOutlined } from "@ant-design/icons";
import { Alert, Avatar, Button, Card, Col, List, Popconfirm, Row, Space, Tag, Tooltip, Typography } from "antd";
import { useCallback, useEffect, useState, type MouseEvent } from "react";
import { useNavigate } from "react-router-dom";

import { deleteConversation } from "../api/chat";
import {
  loadKnowledgeHome,
  type KnowledgeConversation,
  type KnowledgeHome,
} from "../api/knowledge";
import { SpaceIcon } from "./SpaceIcon";

export function KnowledgeDashboard() {
  const navigate = useNavigate();
  const [home, setHome] = useState<KnowledgeHome | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    return loadKnowledgeHome()
      .then((result) => {
        setHome(result);
        setError(null);
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Knowledge spaces could not be loaded");
      });
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

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
              title={
                <Space>
                  <SpaceIcon space={space.id} />
                  {space.label}
                </Space>
              }
              extra={
                <Button
                  type="link"
                  icon={<ArrowRightOutlined />}
                  onClick={() => navigate(`/knowledge/${space.id}`)}
                >
                  Open
                </Button>
              }
            >
              <Typography.Paragraph>{space.summary}</Typography.Paragraph>
              <Space size={4} wrap>
                <Tag>{uploadLabel(space.document_count)}</Tag>
                <Tag>{chatLabel(space.conversation_count)}</Tag>
              </Space>
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
              actions={historyActions(item, (includeFiles) => {
                void deleteConversation(item.id, includeFiles)
                  .then(() => refresh())
                  .catch((reason: unknown) => {
                    setError(
                      reason instanceof Error ? reason.message : "That chat could not be deleted",
                    );
                  });
              })}
            >
              <List.Item.Meta
                avatar={
                  <Avatar
                    icon={<SpaceIcon space={item.space} />}
                    style={{ background: "#f0f5ff", color: "#1677ff" }}
                  />
                }
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

function historyActions(
  item: KnowledgeConversation,
  onDelete: (includeFiles: boolean) => void,
) {
  const stop = (event?: MouseEvent) => event?.stopPropagation();
  return [
    <Tooltip key="chat" title="Delete chat">
      <Popconfirm
        title="Delete this chat?"
        description="The uploaded file stays in its space."
        okText="Delete chat"
        okButtonProps={{ danger: true }}
        onConfirm={() => onDelete(false)}
      >
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          aria-label="Delete chat"
          onClick={stop}
        />
      </Popconfirm>
    </Tooltip>,
    item.file_owned ? (
      <Tooltip key="file" title="Delete chat and file">
        <Popconfirm
          title="Delete this chat and its file?"
          description={
            item.filename
              ? `${item.filename} is removed, and every chat about that file goes with it.`
              : "The file is removed, and every chat about that file goes with it."
          }
          okText="Delete chat and file"
          okButtonProps={{ danger: true }}
          onConfirm={() => onDelete(true)}
        >
          <Button
            type="text"
            danger
            icon={<FileExclamationOutlined />}
            aria-label="Delete chat and file"
            onClick={stop}
          />
        </Popconfirm>
      </Tooltip>
    ) : null,
  ];
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
