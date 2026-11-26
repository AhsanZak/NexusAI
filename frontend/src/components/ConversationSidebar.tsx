import { DeleteOutlined, FileExclamationOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, List, Popconfirm, Space, Tooltip, Typography } from "antd";

import type { ChatConversation } from "../api/chat";

export function ConversationSidebar({
  conversations,
  selectedId,
  onSelect,
  onCreate,
  onDelete,
  onDeleteFile,
  fileName,
}: {
  conversations: ChatConversation[];
  selectedId: string | null;
  onSelect: (conversationId: string) => void;
  onCreate: () => void;
  onDelete: (conversationId: string) => void;
  onDeleteFile?: (conversationId: string) => void;
  fileName?: string | null;
}) {
  return (
    <div className="conversation-sidebar">
      <Button block type="primary" icon={<PlusOutlined />} onClick={onCreate} style={{ marginBottom: 12 }}>
        New chat
      </Button>
      <List
        dataSource={conversations}
        locale={{ emptyText: "No chats yet." }}
        renderItem={(item) => (
          <List.Item
            style={{
              cursor: "pointer",
              background: item.id === selectedId ? "#f0f5ff" : undefined,
              borderRadius: 8,
              paddingInline: 8,
            }}
            onClick={() => onSelect(item.id)}
          >
            <div style={{ minWidth: 0, width: "100%" }}>
              <Typography.Text ellipsis style={{ maxWidth: "100%" }}>
                {item.title}
              </Typography.Text>
              {item.intent_label ? (
                <Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
                  {item.intent_label}
                </Typography.Text>
              ) : null}
              <Space size={0}>
                <Tooltip title="Delete chat">
                  <Popconfirm
                    title="Delete this chat?"
                    description="The uploaded file stays in this space."
                    okText="Delete chat"
                    okButtonProps={{ danger: true }}
                    onConfirm={() => onDelete(item.id)}
                  >
                    <Button
                      type="text"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      aria-label="Delete chat"
                      onClick={(event) => event.stopPropagation()}
                    />
                  </Popconfirm>
                </Tooltip>
                {onDeleteFile ? (
                  <Tooltip title="Delete chat and file">
                    <Popconfirm
                      title="Delete this chat and its file?"
                      description={fileDeleteDetail(fileName)}
                      okText="Delete chat and file"
                      okButtonProps={{ danger: true }}
                      onConfirm={() => onDeleteFile(item.id)}
                    >
                      <Button
                        type="text"
                        danger
                        size="small"
                        icon={<FileExclamationOutlined />}
                        aria-label="Delete chat and file"
                        onClick={(event) => event.stopPropagation()}
                      />
                    </Popconfirm>
                  </Tooltip>
                ) : null}
              </Space>
            </div>
          </List.Item>
        )}
      />
    </div>
  );
}

function fileDeleteDetail(fileName?: string | null): string {
  if (fileName) {
    return `${fileName} is removed, and every chat about that file goes with it.`;
  }
  return "The file is removed, and every chat about that file goes with it.";
}
