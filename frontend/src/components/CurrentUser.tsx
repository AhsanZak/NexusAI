import { Button, Space, Tag, Typography } from "antd";
import { useNavigate } from "react-router-dom";

import { clearSession, loadSession } from "../auth/session";

export function CurrentUser() {
  const navigate = useNavigate();
  const session = loadSession();

  if (!session) {
    return <Tag>Guest</Tag>;
  }

  const admin = session.user.role === "super_admin";
  return (
    <Space size={8} wrap style={{ justifyContent: "flex-end" }}>
      <Tag color={admin ? "blue" : "green"}>{admin ? "Super admin" : "Member"}</Tag>
      <Typography.Text>
        {session.user.display_name}
        <Typography.Text type="secondary"> · {session.user.email}</Typography.Text>
      </Typography.Text>
      <Button
        size="small"
        onClick={() => {
          clearSession();
          navigate("/login");
        }}
      >
        Log out
      </Button>
    </Space>
  );
}
