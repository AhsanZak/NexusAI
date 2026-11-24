import { Alert, Button, Select, Space, Table, Typography } from "antd";
import { useCallback, useEffect, useState } from "react";

import {
  grantDocumentAccess,
  loadAdminLibrary,
  loadDocumentAccess,
  revokeDocumentAccess,
  type DocumentAccess,
  type LibraryDocument,
} from "../api/library";
import { loadUsers } from "../api/users";
import type { SessionUser } from "../auth/session";

export function UploadAdmin() {
  const [documents, setDocuments] = useState<LibraryDocument[]>([]);
  const [users, setUsers] = useState<SessionUser[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [memberId, setMemberId] = useState("");
  const [access, setAccess] = useState<DocumentAccess[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [library, accounts] = await Promise.all([loadAdminLibrary(), loadUsers()]);
    setDocuments(library);
    setUsers(accounts);
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

  async function onGrant() {
    if (!selectedId || !memberId) {
      return;
    }
    try {
      await grantDocumentAccess(selectedId, memberId);
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

  return (
    <div>
      <Typography.Title level={4}>Uploaded documents</Typography.Title>
      <Typography.Paragraph>
        Every member can upload a file and chat with it. This list shows all of those files. A
        member sees another person's file only after you grant access here.
      </Typography.Paragraph>
      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} /> : null}
      <Table
        rowKey="id"
        dataSource={documents}
        pagination={false}
        onRow={(record) => ({ onClick: () => setSelectedId(record.id) })}
        columns={[
          { title: "File", dataIndex: "filename" },
          { title: "Owner", dataIndex: "owner_name" },
          { title: "Email", dataIndex: "owner_email" },
          { title: "Read with", dataIndex: "extractor" },
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
            <Button type="primary" onClick={() => void onGrant()} disabled={!memberId}>
              Grant access
            </Button>
          </Space>
          <Table
            style={{ marginTop: 16 }}
            rowKey="user_id"
            dataSource={access}
            pagination={false}
            columns={[
              { title: "Name", dataIndex: "display_name" },
              { title: "Email", dataIndex: "email" },
              { title: "Kind", render: (_, row) => (row.owner ? "Owner" : "Granted by admin") },
              {
                title: "",
                render: (_, row) =>
                  row.owner ? null : (
                    <Button size="small" danger onClick={() => void onRevoke(row.user_id)}>
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
