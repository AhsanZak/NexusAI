import { RobotOutlined, SendOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Input, Space, Tag, Typography } from "antd";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { askAssistant, type AssistantAnswer } from "../api/assistant";
import {
  deleteConversation,
  loadChatHistory,
  loadConversations,
  type ChatConversation,
  type ChatTurn,
} from "../api/chat";
import { useChatModel } from "../chat/models";
import { AnswerText } from "../components/AnswerText";
import { ChatHistory } from "../components/ChatHistory";
import { ConversationSidebar } from "../components/ConversationSidebar";

export function AssistantPage() {
  const [searchParams] = useSearchParams();
  const requestedConversation = searchParams.get("conversation");
  const { modelId } = useChatModel();
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<AssistantAnswer | null>(null);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const refreshConversations = useCallback(async () => {
    const loaded = await loadConversations();
    setConversations(loaded);
    return loaded;
  }, []);

  useEffect(() => {
    void refreshConversations()
      .then((loaded) => {
        const requested = loaded.find((item) => item.id === requestedConversation);
        const first = requested ?? loaded[0];
        if (first) {
          setSelectedId(first.id);
        }
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Chats could not be loaded");
      });
  }, [refreshConversations, requestedConversation]);

  useEffect(() => {
    if (!selectedId) {
      setHistory([]);
      return;
    }
    void loadChatHistory(selectedId)
      .then(setHistory)
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Chat history could not be loaded");
      });
  }, [selectedId]);

  async function onAsk() {
    const question = prompt.trim();
    if (!question) {
      return;
    }
    setSending(true);
    try {
      const answer = await askAssistant(question, modelId, selectedId);
      setResult(answer);
      setPrompt("");
      setSelectedId(answer.conversation_id);
      setHistory(await loadChatHistory(answer.conversation_id));
      await refreshConversations();
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The assistant is unavailable");
    } finally {
      setSending(false);
    }
  }

  async function onDelete(conversationId: string) {
    try {
      await deleteConversation(conversationId);
      const loaded = await refreshConversations();
      if (selectedId === conversationId) {
        setSelectedId(loaded[0]?.id ?? null);
        setResult(null);
      }
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "That chat could not be deleted");
    }
  }

  const selected = conversations.find((item) => item.id === selectedId);

  return (
    <div className="chat-page">
      <Typography.Title level={3}>
        <RobotOutlined /> Assistant
      </Typography.Title>
      <Typography.Paragraph>
        Each chat keeps its own history, and each question is labeled with the intent understood
        from that chat. Opening a chat sends that chat’s earlier messages with the next question.
        The intent is read first. Documents are opened only when the question asks for them, and then only a document this account may use is placed in the prompt.
      </Typography.Paragraph>
      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} /> : null}
      <div className="chat-layout">
        <ConversationSidebar
          conversations={conversations}
          selectedId={selectedId}
          onSelect={(conversationId) => {
            setSelectedId(conversationId);
            setResult(null);
          }}
          onCreate={() => {
            setSelectedId(null);
            setHistory([]);
            setResult(null);
            setPrompt("");
          }}
          onDelete={(conversationId) => void onDelete(conversationId)}
        />
        <Card className="chat-panel" title={selected?.title ?? "New chat"}>
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <div className="chat-thread">
              <ChatHistory messages={history} />
              {result ? (
                <Card title={`Answer for ${result.display_name}`} style={{ marginTop: 16 }}>
                  <Tag style={{ marginBottom: 12 }}>{result.intent_label}</Tag>
                  {result.status === "success" && result.answer ? (
                    <AnswerText text={result.answer} />
                  ) : (
                    <Typography.Paragraph>
                      {result.error_message || "The model call failed."}
                    </Typography.Paragraph>
                  )}
                  <Space direction="vertical">
                    {result.documents.map((item) => (
                      <div key={item.object_id}>
                        <Tag color={item.allowed ? "success" : "error"}>
                          {item.allowed ? "Sent to the model" : "Withheld"}
                        </Tag>
                        <Typography.Text>{item.object_name}</Typography.Text>
                      </div>
                    ))}
                  </Space>
                </Card>
              ) : null}
            </div>
            <div className="composer">
              <Input.TextArea
                rows={4}
                value={prompt}
                placeholder="Ask about the documents this account can use"
                onChange={(event) => setPrompt(event.target.value)}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={() => void onAsk()}
                loading={sending}
                disabled={!prompt.trim()}
                style={{ marginTop: 12 }}
              >
                Ask
              </Button>
            </div>
          </Space>
        </Card>
      </div>
    </div>
  );
}
