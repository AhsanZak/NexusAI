import { Tag, Typography } from "antd";

import type { ChatTurn } from "../api/chat";
import { AnswerText } from "./AnswerText";

export function ChatHistory({ messages }: { messages: ChatTurn[] }) {
  if (messages.length === 0) {
    return <Typography.Text type="secondary">No messages yet.</Typography.Text>;
  }
  return (
    <div style={{ maxHeight: 480, overflow: "auto" }}>
      {messages.map((message) => (
        <div
          key={message.id}
          style={{
            marginBottom: 12,
            background: message.role === "assistant" ? "#f7f8fa" : undefined,
            borderRadius: 8,
            padding: message.role === "assistant" ? "8px 12px" : undefined,
          }}
        >
          <Typography.Text strong>{message.role === "user" ? "You" : message.model_name}</Typography.Text>
          {message.intent_label ? (
            <Tag style={{ marginLeft: 8 }}>{message.intent_label}</Tag>
          ) : null}
          <div style={{ marginTop: 4 }}>
            <AnswerText text={message.content} />
          </div>
        </div>
      ))}
    </div>
  );
}
