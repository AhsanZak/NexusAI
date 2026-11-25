import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import { Alert, Button, Form, Popconfirm, Select, Table, Typography } from "antd";
import { useCallback, useEffect, useState } from "react";

import {
  createPermission,
  deletePermission,
  loadPermissions,
  updatePermission,
  type PermissionGrant,
  type PermissionList,
} from "../api/access";
import { loadUsers } from "../api/users";
import type { SessionUser } from "../auth/session";

export function PermissionAdmin() {
  const [data, setData] = useState<PermissionList | null>(null);
  const [users, setUsers] = useState<SessionUser[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [who, setWho] = useState("guest");
  const [objectId, setObjectId] = useState("");
  const [relation, setRelation] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [permissions, accounts] = await Promise.all([loadPermissions(), loadUsers()]);
      setData(permissions);
      setUsers(accounts);
      setObjectId((current) => current || permissions.catalog[0]?.object_id || "");
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Permissions could not be loaded");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const selected = data?.catalog.find((item) => item.object_id === objectId);
  const relations = selected?.relations ?? [];

  useEffect(() => {
    if (!selected) {
      return;
    }
    setRelation((current) => (selected.relations.includes(current) ? current : selected.releasing_relation));
  }, [selected]);

  async function onGrant() {
    if (!selected || !relation) {
      return;
    }
    try {
      await createPermission({
        subject_kind: who === "guest" ? "guest" : "member",
        user_id: who === "guest" ? undefined : who,
        relation,
        object_id: selected.object_id,
      });
      setError(null);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not grant that permission");
    }
  }

  async function onRelation(grant: PermissionGrant, next: string) {
    try {
      await updatePermission(grant.id, next);
      setError(null);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update that permission");
    }
  }

  async function onRemove(grant: PermissionGrant) {
    try {
      await deletePermission(grant.id);
      setError(null);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not remove that permission");
    }
  }

  return (
    <div>
      <Typography.Title level={4}>OpenFGA permissions</Typography.Title>
      <Typography.Paragraph>
        Create, update, and remove grants here. Each row is written to OpenFGA. A signed-in member
        is checked as that member. Guest is a separate subject, user:guest, with no login. Uploaded
        files are in this list too. A file uses viewer, analyst, or auditor. The AI model and
        analysis use can_use.
      </Typography.Paragraph>
      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} /> : null}
      <Form layout="inline" style={{ marginBottom: 16, rowGap: 8 }}>
        <Form.Item label="Who">
          <Select
            value={who}
            style={{ minWidth: 260 }}
            onChange={setWho}
            options={[
              { value: "guest", label: "Guest" },
              ...users.map((user) => ({
                value: user.id,
                label: `${user.display_name} · ${user.email}`,
              })),
            ]}
          />
        </Form.Item>
        <Form.Item label="Object">
          <Select
            value={objectId || undefined}
            style={{ minWidth: 240 }}
            onChange={setObjectId}
            options={(data?.catalog ?? []).map((item) => ({
              value: item.object_id,
              label: `${item.name} · ${item.object_type}`,
            }))}
          />
        </Form.Item>
        <Form.Item label="Relation">
          <Select
            value={relation || undefined}
            style={{ minWidth: 140 }}
            onChange={setRelation}
            options={relations.map((item) => ({ value: item, label: item }))}
          />
        </Form.Item>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => void onGrant()} disabled={!objectId || !relation}>
          Grant
        </Button>
      </Form>
      <Table
        rowKey="id"
        loading={loading}
        dataSource={data?.grants ?? []}
        pagination={false}
        columns={[
          {
            title: "Who",
            render: (_, grant) => (grant.email ? `${grant.display_name} · ${grant.email}` : grant.display_name),
          },
          { title: "Access as", dataIndex: "actor" },
          { title: "Object", dataIndex: "object_name" },
          { title: "Type", dataIndex: "object_type" },
          {
            title: "Relation",
            render: (_, grant) => {
              const item = data?.catalog.find((entry) => entry.object_id === grant.object_id);
              return (
                <Select
                  value={grant.relation}
                  style={{ minWidth: 140 }}
                  options={(item?.relations ?? [grant.relation]).map((value) => ({
                    value,
                    label: value,
                  }))}
                  onChange={(value) => void onRelation(grant, value)}
                />
              );
            },
          },
          {
            title: "",
            width: 120,
            render: (_, grant) => (
              <Popconfirm title="Remove this permission?" onConfirm={() => void onRemove(grant)}>
                <Button danger size="small" icon={<DeleteOutlined />}>
                  Remove
                </Button>
              </Popconfirm>
            ),
          },
        ]}
      />
    </div>
  );
}
