import { SendOutlined, UploadOutlined } from "@ant-design/icons";
import { Alert, Avatar, Button, Card, Input, List, Space, Tag, Typography, Upload } from "antd";
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
import { loadSession } from "../auth/session";
import { useChatModel } from "../chat/models";
import { ChatHistory } from "../components/ChatHistory";
import { ConversationSidebar } from "../components/ConversationSidebar";
import { DeviceActions } from "../components/DeviceActions";
import { SpaceIcon } from "../components/SpaceIcon";

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
        <Space>
          <SpaceIcon space={space} />
          {meta?.label ?? "Knowledge"}
        </Space>
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
        <Button type="primary" icon={<UploadOutlined />} loading={uploading} disabled={!meta}>
          Upload into {meta?.label ?? "this space"}
        </Button>
      </Upload>
      <DeviceActions
        busy={uploading}
        onFile={(file) => void onUpload(file)}
        shareTitle={selected?.filename}
        shareTextValue={selected ? `${selected.filename}\n${selected.excerpt}` : undefined}
        onMessage={setError}
      />
      <List
        className="file-list"
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
            <Space align="start" style={{ width: "100%", minWidth: 0 }}>
              <Avatar icon={<SpaceIcon space={item.space} />} style={{ background: "#f0f5ff", color: "#1677ff" }} />
              <Space direction="vertical" size={2} style={{ minWidth: 0, flex: 1 }}>
                <Space wrap>
                  <Typography.Text strong>{item.filename}</Typography.Text>
                  {item.shared ? <Tag color="blue">Shared with you</Tag> : <Tag color="green">Yours</Tag>}
                </Space>
                <Typography.Text type="secondary">
                  {item.owner_name} · {item.extractor} · {item.excerpt}
                </Typography.Text>
              </Space>
            </Space>
          </List.Item>
        )}
      />
      {selected ? (
        <Card title={`Ask about ${selected.filename}`} style={{ marginTop: 16 }}>
          <div className="chat-layout">
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
              fileName={selected.filename}
              onDeleteFile={
                selected.owner_id === loadSession()?.user.id
                  ? (id) => {
                      void deleteConversation(id, true)
                        .then(() => refresh())
                        .then(() => {
                          setConversationId(null);
                          setHistory([]);
                          setError(null);
                        })
                        .catch((reason: unknown) => {
                          setError(
                            reason instanceof Error
                              ? reason.message
                              : "That chat and file could not be deleted",
                          );
                        });
                    }
                  : undefined
              }
            />
            <Space className="chat-panel" direction="vertical" size="middle">
              <ChatHistory messages={history} />
              <div className="composer">
                <Input.TextArea
                  rows={3}
                  value={prompt}
                  placeholder={meta?.placeholder}
                  onChange={(event) => setPrompt(event.target.value)}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={() => void onAsk()}
                  loading={asking}
                  disabled={!prompt.trim()}
                  style={{ marginTop: 12 }}
                >
                  Ask
                </Button>
              </div>
            </Space>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
