import { RobotOutlined, UserOutlined } from "@ant-design/icons";
import { Avatar, Space, Tag, Typography } from "antd";

import type { ChatTurn } from "../api/chat";
import { AnswerText } from "./AnswerText";

export function ChatHistory({ messages }: { messages: ChatTurn[] }) {
  if (messages.length === 0) {
    return (
      <div className="chat-history">
        <Typography.Text type="secondary">No messages yet.</Typography.Text>
      </div>
    );
  }
  return (
    <div className="chat-history">
      {messages.map((message) => {
        const assistant = message.role === "assistant";
        return (
          <div
            key={message.id}
            style={{
              marginBottom: 12,
              background: assistant ? "#f7f8fa" : undefined,
              borderRadius: 8,
              padding: assistant ? "10px 12px" : "4px 0",
            }}
          >
            <Space size={8} align="center">
              <Avatar
                size="small"
                icon={assistant ? <RobotOutlined /> : <UserOutlined />}
                style={{ background: assistant ? "#1677ff" : "#87d068" }}
              />
              <Typography.Text strong>{assistant ? message.model_name : "You"}</Typography.Text>
              {message.intent_label ? <Tag>{message.intent_label}</Tag> : null}
            </Space>
            <div style={{ marginTop: 6, paddingInlineStart: 32 }}>
              <AnswerText text={message.content} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
