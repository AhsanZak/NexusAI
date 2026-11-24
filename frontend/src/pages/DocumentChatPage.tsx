import { FileAddOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Input, List, Space, Tag, Typography, Upload } from "antd";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import {
  deleteConversation,
  loadChatHistory,
  loadConversations,
  type ChatConversation,
  type ChatTurn,
} from "../api/chat";
import { loadKnowledgeHome, type KnowledgeSpace } from "../api/knowledge";
import { askLibrary, loadLibrary, uploadLibraryFile, type LibraryDocument } from "../api/library";
import { useChatModel } from "../chat/models";
import { ChatHistory } from "../components/ChatHistory";
import { ConversationSidebar } from "../components/ConversationSidebar";

export function DocumentChatPage() {
  const { space = "" } = useParams();
  const [searchParams] = useSearchParams();
  const requestedDocument = searchParams.get("document");
  const requestedConversation = searchParams.get("conversation");
  const { modelId } = useChatModel();
  const [meta, setMeta] = useState<KnowledgeSpace | null>(null);
  const [documents, setDocuments] = useState<LibraryDocument[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [prompt, setPrompt] = useState("");
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(requestedConversation);
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);

  useEffect(() => {
    void loadKnowledgeHome()
      .then((home) => {
        const found = home.spaces.find((item) => item.id === space) ?? null;
        setMeta(found);
        if (!found) {
          setError("That knowledge space does not exist");
        }
        setPrompt((current) => current || found?.placeholder || "");
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "The space could not be loaded");
      });
  }, [space]);

  const refresh = useCallback(async () => {
    const loaded = await loadLibrary(space);
    setDocuments(loaded);
    setSelectedId((current) => {
      if (current && loaded.some((item) => item.id === current)) {
        return current;
      }
      if (requestedDocument && loaded.some((item) => item.id === requestedDocument)) {
        return requestedDocument;
      }
      return loaded[0]?.id || "";
    });
  }, [requestedDocument, space]);

  useEffect(() => {
    if (!space) {
      return;
    }
    void refresh().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Documents could not be loaded");
    });
  }, [refresh, space]);

  useEffect(() => {
    if (!selectedId) {
      setConversations([]);
      setConversationId(null);
      setHistory([]);
      return;
    }
    void loadConversations(selectedId)
      .then((loaded) => {
        setConversations(loaded);
        const match = loaded.find((item) => item.id === requestedConversation);
        setConversationId(match?.id ?? loaded[0]?.id ?? null);
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Chats could not be loaded");
      });
  }, [requestedConversation, selectedId]);

  useEffect(() => {
    if (!conversationId) {
      setHistory([]);
      return;
    }
    void loadChatHistory(conversationId)
      .then(setHistory)
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Chat history could not be loaded");
      });
  }, [conversationId]);

  async function onUpload(file: File) {
    setUploading(true);
    try {
      const saved = await uploadLibraryFile(file, space);
      setError(null);
      await refresh();
      setSelectedId(saved.id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The file could not be read");
    } finally {
      setUploading(false);
    }
  }

  async function onAsk() {
    if (!selectedId || !prompt.trim()) {
      return;
    }
    setAsking(true);
    try {
      const answer = await askLibrary(selectedId, prompt, modelId, conversationId);
      setConversationId(answer.conversation_id);
      setConversations(await loadConversations(selectedId));
      setHistory(await loadChatHistory(answer.conversation_id));
      setPrompt("");
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The document chat failed");
    } finally {
      setAsking(false);
    }
  }

  const selected = documents.find((item) => item.id === selectedId);

  return (
    <div>
      <Typography.Title level={3}>
        <FileAddOutlined /> {meta?.label ?? "Knowledge"}
      </Typography.Title>
      <Typography.Paragraph>
        {meta?.summary ?? "Open a knowledge space from the dashboard."}{" "}
        <Link to="/knowledge">All spaces</Link>
      </Typography.Paragraph>
      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} /> : null}
      <Upload
        accept={meta?.extensions.join(",") ?? ""}
        maxCount={1}
        showUploadList={false}
        beforeUpload={(file) => {
          void onUpload(file);
          return false;
        }}
      >
        <Button type="primary" loading={uploading} disabled={!meta}>
          Upload into {meta?.label ?? "this space"}
        </Button>
      </Upload>
      <List
        style={{ marginTop: 16 }}
        dataSource={documents}
        locale={{ emptyText: "No files in this space yet." }}
        renderItem={(item) => (
          <List.Item
            style={{ cursor: "pointer", background: item.id === selectedId ? "#f0f5ff" : undefined }}
            onClick={() => {
              setSelectedId(item.id);
              setConversationId(null);
            }}
          >
            <Space direction="vertical" size={2}>
              <Space>
                <Typography.Text strong>{item.filename}</Typography.Text>
                {item.shared ? <Tag>Shared with you</Tag> : <Tag>Yours</Tag>}
              </Space>
              <Typography.Text type="secondary">
                {item.owner_name} · {item.excerpt}
              </Typography.Text>
            </Space>
          </List.Item>
        )}
      />
      {selected ? (
        <Card title={`Ask about ${selected.filename}`} style={{ marginTop: 16 }}>
          <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
            <ConversationSidebar
              conversations={conversations}
              selectedId={conversationId}
              onSelect={setConversationId}
              onCreate={() => {
                setConversationId(null);
                setHistory([]);
                setPrompt("");
              }}
              onDelete={(id) => {
                void deleteConversation(id)
                  .then(() => loadConversations(selectedId))
                  .then((loaded) => {
                    setConversations(loaded);
                    if (conversationId === id) {
                      setConversationId(loaded[0]?.id ?? null);
                    }
                  })
                  .catch((reason: unknown) => {
                    setError(reason instanceof Error ? reason.message : "That chat could not be deleted");
                  });
              }}
            />
            <Space direction="vertical" size="middle" style={{ flex: 1, minWidth: 0 }}>
              <ChatHistory messages={history} />
              <Input.TextArea
                rows={3}
                value={prompt}
                placeholder={meta?.placeholder}
                onChange={(event) => setPrompt(event.target.value)}
              />
              <Button type="primary" onClick={() => void onAsk()} loading={asking} disabled={!prompt.trim()}>
                Ask
              </Button>
            </Space>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
