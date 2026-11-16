import {
  ApartmentOutlined,
  BarChartOutlined,
  BugOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  RobotOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { Layout, Menu, Typography } from "antd";
import { useState } from "react";
import { Link, Route, Routes, useLocation } from "react-router-dom";

import { DebugPage } from "../pages/DebugPage";
import { OverviewPage } from "../pages/OverviewPage";
import { PlaceholderPage } from "../pages/PlaceholderPage";

const { Header, Sider, Content } = Layout;

const items = [
  { key: "/", icon: <DashboardOutlined />, label: <Link to="/">Overview</Link> },
  { key: "/documents", icon: <FileSearchOutlined />, label: <Link to="/documents">Documents</Link> },
  { key: "/assistant", icon: <RobotOutlined />, label: <Link to="/assistant">Assistant</Link> },
  { key: "/analytics", icon: <BarChartOutlined />, label: <Link to="/analytics">Analytics</Link> },
  { key: "/agents", icon: <ApartmentOutlined />, label: <Link to="/agents">Agents</Link> },
  { key: "/admin", icon: <TeamOutlined />, label: <Link to="/admin">Admin</Link> },
  { key: "/debug", icon: <BugOutlined />, label: <Link to="/debug">OpenAI debug</Link> },
];

export function AppShell() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const selected = items.some((item) => item.key === location.pathname) ? location.pathname : "/";

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="light" width={220}>
        <Typography.Title level={4} style={{ margin: "16px 20px" }}>
          {collapsed ? "N" : "NexusAI"}
        </Typography.Title>
        <Menu mode="inline" selectedKeys={[selected]} items={items} />
      </Sider>
      <Layout>
        <Header style={{ background: "#fff", padding: "0 24px", borderBottom: "1px solid #f0f0f0" }}>
          <Typography.Text type="secondary">Enterprise knowledge, analytics, and automation</Typography.Text>
        </Header>
        <Content style={{ margin: 24 }}>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route
              path="/documents"
              element={
                <PlaceholderPage
                  title="Document intelligence"
                  milestone="Document upload, chunking, and permission-checked retrieval"
                />
              }
            />
            <Route
              path="/assistant"
              element={
                <PlaceholderPage
                  title="Knowledge assistant"
                  milestone="Permission-aware RAG with citations and streaming"
                />
              }
            />
            <Route
              path="/analytics"
              element={
                <PlaceholderPage
                  title="NL2SQL analytics"
                  milestone="Read-only natural-language queries over the Olist warehouse"
                />
              }
            />
            <Route
              path="/agents"
              element={
                <PlaceholderPage
                  title="AI agents"
                  milestone="Research, analyst, and report agents with an approval gate"
                />
              }
            />
            <Route
              path="/admin"
              element={
                <PlaceholderPage
                  title="Administration"
                  milestone="Organizations, users, departments, and OpenFGA permissions"
                />
              }
            />
            <Route path="/debug" element={<DebugPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}
