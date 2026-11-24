import { Tag, Typography } from "antd";

import type { ChatTurn } from "../api/chat";

export function ChatHistory({ messages }: { messages: ChatTurn[] }) {
  if (messages.length === 0) {
    return <Typography.Text type="secondary">No messages yet.</Typography.Text>;
  }
  return (
    <div style={{ maxHeight: 480, overflow: "auto" }}>
      {messages.map((message) => (
        <div key={message.id} style={{ marginBottom: 12 }}>
          <Typography.Text strong>{message.role === "user" ? "You" : message.model_name}</Typography.Text>
          {message.intent_label ? (
            <Tag style={{ marginLeft: 8 }}>{message.intent_label}</Tag>
          ) : null}
          <Typography.Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
            {message.content}
          </Typography.Paragraph>
        </div>
      ))}
    </div>
  );
}
