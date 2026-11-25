import { DeleteOutlined, PlusOutlined, UploadOutlined } from "@ant-design/icons";
import { Alert, Button, Select, Space, Table, Typography, Upload } from "antd";
import { useCallback, useEffect, useState } from "react";

import { loadKnowledgeHome, type KnowledgeSpace } from "../api/knowledge";
import {
  grantDocumentAccess,
  loadAdminLibrary,
  loadDocumentAccess,
  revokeDocumentAccess,
  uploadLibraryFile,
  type DocumentAccess,
  type LibraryDocument,
} from "../api/library";
import { loadUsers } from "../api/users";
import type { SessionUser } from "../auth/session";

const RELATIONS = [
  { value: "viewer", label: "Viewer" },
  { value: "analyst", label: "Analyst" },
  { value: "auditor", label: "Auditor" },
];

export function UploadAdmin() {
  const [documents, setDocuments] = useState<LibraryDocument[]>([]);
  const [users, setUsers] = useState<SessionUser[]>([]);
  const [spaces, setSpaces] = useState<KnowledgeSpace[]>([]);
  const [space, setSpace] = useState("document");
  const [selectedId, setSelectedId] = useState("");
  const [memberId, setMemberId] = useState("");
  const [relation, setRelation] = useState("viewer");
  const [access, setAccess] = useState<DocumentAccess[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const refresh = useCallback(async () => {
    const [library, accounts, home] = await Promise.all([
      loadAdminLibrary(),
      loadUsers(),
      loadKnowledgeHome(),
    ]);
    setDocuments(library);
    setUsers(accounts);
    setSpaces(home.spaces);
    setSpace((current) => home.spaces.find((item) => item.id === current)?.id || home.spaces[0]?.id || "document");
    setSelectedId((current) => current || library[0]?.id || "");
  }, []);

  useEffect(() => {
    void refresh().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Uploaded documents could not be loaded");
    });
  }, [refresh]);

  useEffect(() => {
    if (!selectedId) {
      setAccess([]);
      return;
    }
    void loadDocumentAccess(selectedId)
      .then(setAccess)
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Access could not be loaded");
      });
  }, [selectedId]);

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

  async function onGrant(userId = memberId, nextRelation = relation) {
    if (!selectedId || !userId) {
      return;
    }
    try {
      await grantDocumentAccess(selectedId, userId, nextRelation);
      setAccess(await loadDocumentAccess(selectedId));
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Access could not be granted");
    }
  }

  async function onRevoke(userId: string) {
    try {
      await revokeDocumentAccess(selectedId, userId);
      setAccess(await loadDocumentAccess(selectedId));
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Access could not be removed");
    }
  }

  const selectedSpace = spaces.find((item) => item.id === space);

  return (
    <div>
      <Typography.Title level={4}>Uploaded documents</Typography.Title>
      <Typography.Paragraph>
        Add a file while signed in as admin, then grant each member an OpenFGA relation. Viewer,
        analyst, and auditor can open that file. A member with none of those relations cannot see it.
      </Typography.Paragraph>
      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} /> : null}
      <Space wrap style={{ marginBottom: 16 }}>
        <Select
          value={space}
          style={{ minWidth: 180 }}
          onChange={setSpace}
          options={spaces.map((item) => ({ value: item.id, label: item.label }))}
        />
        <Upload
          accept={selectedSpace?.extensions.join(",") ?? ""}
          maxCount={1}
          showUploadList={false}
          beforeUpload={(file) => {
            void onUpload(file);
            return false;
          }}
        >
          <Button type="primary" icon={<UploadOutlined />} loading={uploading} disabled={!selectedSpace}>
            Add document
          </Button>
        </Upload>
      </Space>
      <Table
        rowKey="id"
        dataSource={documents}
        pagination={false}
        onRow={(record) => ({ onClick: () => setSelectedId(record.id) })}
        columns={[
          { title: "File", dataIndex: "filename" },
          { title: "Space", dataIndex: "space" },
          { title: "Owner", dataIndex: "owner_name" },
          { title: "Email", dataIndex: "owner_email" },
        ]}
      />
      {selectedId ? (
        <div style={{ marginTop: 16 }}>
          <Space wrap>
            <Select
              value={memberId || undefined}
              placeholder="Member"
              style={{ minWidth: 280 }}
              onChange={setMemberId}
              options={users
                .filter((user) => user.role === "member")
                .map((user) => ({ value: user.id, label: `${user.display_name} · ${user.email}` }))}
            />
            <Select value={relation} style={{ minWidth: 140 }} onChange={setRelation} options={RELATIONS} />
            <Button type="primary" icon={<PlusOutlined />} onClick={() => void onGrant()} disabled={!memberId}>
              Grant access
            </Button>
          </Space>
          <Table
            style={{ marginTop: 16 }}
            rowKey={(row) => `${row.user_id}-${row.relation}`}
            dataSource={access}
            pagination={false}
            columns={[
              { title: "Name", dataIndex: "display_name" },
              { title: "Email", dataIndex: "email" },
              { title: "Kind", render: (_, row) => (row.owner ? "Owner" : "Granted by admin") },
              {
                title: "OpenFGA relation",
                render: (_, row) => (
                  <Select
                    value={row.relation}
                    style={{ minWidth: 140 }}
                    disabled={row.owner}
                    options={RELATIONS}
                    onChange={(value) => void onGrant(row.user_id, value)}
                  />
                ),
              },
              {
                title: "",
                render: (_, row) =>
                  row.owner ? null : (
                    <Button size="small" danger icon={<DeleteOutlined />} onClick={() => void onRevoke(row.user_id)}>
                      Remove access
                    </Button>
                  ),
              },
            ]}
          />
        </div>
      ) : null}
    </div>
  );
}
