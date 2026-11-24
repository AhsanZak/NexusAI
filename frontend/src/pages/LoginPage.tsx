import { LoginOutlined } from "@ant-design/icons";
import { Button, Card, Form, Input, Typography } from "antd";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { login } from "../api/users";
import { saveSession } from "../auth/session";
import { CurrentUser } from "../components/CurrentUser";

export function LoginPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onFinish(values: { email: string; password: string }) {
    setSubmitting(true);
    try {
      const result = await login(values.email, values.password);
      saveSession({ token: result.access_token, user: result.user });
      navigate("/");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#f5f5f5" }}>
      <div style={{ position: "fixed", top: 16, right: 24 }}>
        <CurrentUser />
      </div>
      <Card title="NexusAI" style={{ width: 380 }}>
        <Typography.Paragraph type="secondary">Sign in with your database account.</Typography.Paragraph>
        <Form layout="vertical" onFinish={(values) => void onFinish(values)} requiredMark={false}>
          <Form.Item label="Email" name="email" rules={[{ required: true, type: "email" }]}>
            <Input autoComplete="username" />
          </Form.Item>
          <Form.Item label="Password" name="password" rules={[{ required: true }]}>
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          {error ? (
            <Typography.Paragraph type="danger" style={{ marginBottom: 12 }}>
              {error}
            </Typography.Paragraph>
          ) : null}
          <Button type="primary" htmlType="submit" icon={<LoginOutlined />} block loading={submitting}>
            Log in
          </Button>
        </Form>
      </Card>
    </div>
  );
}
