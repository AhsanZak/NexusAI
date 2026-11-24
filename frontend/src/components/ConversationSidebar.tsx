import { Button, List, Typography } from "antd";

import type { ChatConversation } from "../api/chat";

export function ConversationSidebar({
  conversations,
  selectedId,
  onSelect,
  onCreate,
  onDelete,
}: {
  conversations: ChatConversation[];
  selectedId: string | null;
  onSelect: (conversationId: string) => void;
  onCreate: () => void;
  onDelete: (conversationId: string) => void;
}) {
  return (
    <div style={{ width: 260, flex: "0 0 260px" }}>
      <Button block onClick={onCreate} style={{ marginBottom: 12 }}>
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
              paddingInline: 8,
            }}
            onClick={() => onSelect(item.id)}
            actions={[
              <Button
                key="delete"
                type="link"
                danger
                onClick={(event) => {
                  event.stopPropagation();
                  onDelete(item.id);
                }}
              >
                Delete
              </Button>,
            ]}
          >
            <div style={{ minWidth: 0 }}>
              <Typography.Text ellipsis style={{ maxWidth: 150 }}>
                {item.title}
              </Typography.Text>
              {item.intent_label ? (
                <Typography.Text type="secondary" style={{ display: "block", fontSize: 12 }}>
                  {item.intent_label}
                </Typography.Text>
              ) : null}
            </div>
          </List.Item>
        )}
      />
    </div>
  );
}
