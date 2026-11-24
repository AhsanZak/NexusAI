import { UserAddOutlined } from "@ant-design/icons";
import { Alert, Button, Form, Input, Table, Typography } from "antd";
import { useCallback, useEffect, useState } from "react";

import { createUser, loadUsers } from "../api/users";
import { loadSession, type SessionUser } from "../auth/session";

export function UserAdmin() {
  const session = loadSession();
  const [users, setUsers] = useState<SessionUser[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm<{ display_name: string; email: string; password: string }>();

  const refresh = useCallback(async () => {
    if (session?.user.role !== "super_admin") {
      return;
    }
    setLoading(true);
    try {
      setUsers(await loadUsers());
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load users");
    } finally {
      setLoading(false);
    }
  }, [session?.user.role]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (session?.user.role !== "super_admin") {
    return <Alert type="info" showIcon message="Only a super admin can add users." />;
  }

  async function onAdd(values: { display_name: string; email: string; password: string }) {
    try {
      await createUser(values);
      form.resetFields();
      setError(null);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not add the user");
    }
  }

  return (
    <div>
      <Typography.Title level={4}>Users</Typography.Title>
      <Typography.Paragraph>
        Signed in as {session.user.email}. New accounts are stored in PostgreSQL and can log in with the email and password you set.
      </Typography.Paragraph>
      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} /> : null}
      <Form form={form} layout="vertical" onFinish={(values) => void onAdd(values)} style={{ maxWidth: 480 }}>
        <Form.Item label="Name" name="display_name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Email" name="email" rules={[{ required: true, type: "email" }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Password" name="password" rules={[{ required: true, min: 8 }]}>
          <Input.Password />
        </Form.Item>
        <Button type="primary" htmlType="submit" icon={<UserAddOutlined />}>
          Add user
        </Button>
      </Form>
      <Table
        style={{ marginTop: 24 }}
        rowKey="id"
        loading={loading}
        dataSource={users}
        pagination={false}
        columns={[
          { title: "Name", dataIndex: "display_name" },
          { title: "Email", dataIndex: "email" },
          { title: "Role", dataIndex: "role" },
        ]}
      />
    </div>
  );
}
