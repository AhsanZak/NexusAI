import { LogoutOutlined, UserOutlined } from "@ant-design/icons";
import { Avatar, Button, Space, Tag, Typography } from "antd";
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
    <Space className="current-user" size={8} wrap style={{ justifyContent: "flex-end" }}>
      <Avatar size="small" icon={<UserOutlined />} />
      <Tag color={admin ? "blue" : "green"}>{admin ? "Super admin" : "Member"}</Tag>
      <Typography.Text className="current-user-name">
        {session.user.display_name}
        <Typography.Text type="secondary"> · {session.user.email}</Typography.Text>
      </Typography.Text>
      <Button
        className="current-user-logout"
        size="small"
        aria-label="Log out"
        icon={<LogoutOutlined />}
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
