import {
  ApartmentOutlined,
  BarChartOutlined,
  BugOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  ReadOutlined,
  RobotOutlined,
  TeamOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Alert, Card, Layout, Menu, Typography } from "antd";
import { useEffect, useState, type ReactNode } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { featureAllowed, loadMyAccess, type MyAccess } from "../api/access";
import { loadSession } from "../auth/session";
import { ChatModelProvider } from "../chat/models";
import { CurrentUser } from "../components/CurrentUser";
import { KnowledgeDashboard } from "../components/KnowledgeDashboard";
import { ModelRouteBar } from "../components/ModelRouteBar";
import { AdminPage } from "../pages/AdminPage";
import { AnalyticsPage } from "../pages/AnalyticsPage";
import { AssistantPage } from "../pages/AssistantPage";
import { DebugPage } from "../pages/DebugPage";
import { DocumentChatPage } from "../pages/DocumentChatPage";
import { DocumentsPage } from "../pages/DocumentsPage";
import { MemberHomePage } from "../pages/MemberHomePage";
import { OverviewPage } from "../pages/OverviewPage";
import { PlaceholderPage } from "../pages/PlaceholderPage";

const { Header, Sider, Content } = Layout;

export function AppShell() {
  const location = useLocation();
  const session = loadSession();
  const admin = session?.user.role === "super_admin";
  const [collapsed, setCollapsed] = useState(false);
  const [access, setAccess] = useState<MyAccess | null>(null);
  const [accessReady, setAccessReady] = useState(admin);

  useEffect(() => {
    if (admin) {
      return;
    }
    void loadMyAccess()
      .then((result) => {
        setAccess(result);
        setAccessReady(true);
      })
      .catch(() => setAccessReady(true));
  }, [admin]);

  const canModel = featureAllowed(access, "feature:ai-model", admin);
  const canAnalysis = featureAllowed(access, "feature:analysis", admin);
  const items = navItems(admin, canModel, canAnalysis);
  const selected = location.pathname.startsWith("/knowledge")
    ? "/knowledge"
    : items.some((item) => item.key === location.pathname)
      ? location.pathname
      : "/";

  return (
    <ChatModelProvider>
    <Layout style={{ minHeight: "100vh" }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="light" width={220}>
        <Typography.Title level={4} style={{ margin: "16px 20px" }}>
          {collapsed ? "N" : "NexusAI"}
        </Typography.Title>
        <Menu mode="inline" selectedKeys={[selected]} items={items} />
      </Sider>
      <Layout>
        <Header
          style={{
            background: "#fff",
            padding: "12px 24px",
            height: "auto",
            lineHeight: "normal",
            borderBottom: "1px solid #f0f0f0",
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <ModelRouteBar />
            </div>
            <CurrentUser />
          </div>
        </Header>
        <Content style={{ margin: 24 }}>
          <Routes>
            <Route path="/" element={admin ? <OverviewPage /> : <MemberHomePage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/knowledge" element={<KnowledgeDashboard />} />
            <Route path="/knowledge/:space" element={<DocumentChatPage />} />
            <Route path="/library" element={<Navigate to="/knowledge" replace />} />
            <Route
              path="/assistant"
              element={
                <Gated
                  ready={accessReady}
                  allowed={canModel}
                  title="AI model"
                  message="You are signed in as a member. The AI model permission is not granted for this account."
                >
                  <AssistantPage />
                </Gated>
              }
            />
            <Route
              path="/analytics"
              element={
                <Gated
                  ready={accessReady}
                  allowed={canAnalysis}
                  title="Analysis"
                  message="You are signed in as a member. Analysis permission is not granted for this account."
                >
                  <AnalyticsPage />
                </Gated>
              }
            />
            <Route
              path="/agents"
              element={
                admin ? (
                  <PlaceholderPage
                    title="AI agents"
                    milestone="Research, analyst, and report agents with an approval gate"
                  />
                ) : (
                  <Denied title="Agents" message="Agents stay on the admin menu." />
                )
              }
            />
            <Route
              path="/admin"
              element={
                admin ? (
                  <AdminPage />
                ) : (
                  <Denied
                    title="Admin"
                    message="Only a super admin can add members and change OpenFGA permissions."
                  />
                )
              }
            />
            <Route
              path="/debug"
              element={
                admin ? (
                  <DebugPage />
                ) : (
                  <Denied title="Model status" message="Model status stays on the admin menu." />
                )
              }
            />
          </Routes>
        </Content>
      </Layout>
    </Layout>
    </ChatModelProvider>
  );
}

function navItems(admin: boolean, canModel: boolean, canAnalysis: boolean) {
  const link = (to: string, text: string) => <Link to={to}>{text}</Link>;
  const items: { key: string; icon: ReactNode; label: ReactNode }[] = admin
    ? [
        { key: "/", icon: <DashboardOutlined />, label: link("/", "Overview") },
        { key: "/knowledge", icon: <ReadOutlined />, label: link("/knowledge", "Knowledge") },
        { key: "/documents", icon: <FileSearchOutlined />, label: link("/documents", "Documents") },
        { key: "/assistant", icon: <RobotOutlined />, label: link("/assistant", "Assistant") },
        { key: "/analytics", icon: <BarChartOutlined />, label: link("/analytics", "Analysis") },
        { key: "/agents", icon: <ApartmentOutlined />, label: link("/agents", "Agents") },
        { key: "/admin", icon: <TeamOutlined />, label: link("/admin", "Admin") },
        { key: "/debug", icon: <BugOutlined />, label: link("/debug", "Model status") },
      ]
    : [
        { key: "/", icon: <UserOutlined />, label: link("/", "My page") },
        { key: "/knowledge", icon: <ReadOutlined />, label: link("/knowledge", "Knowledge") },
        { key: "/documents", icon: <FileSearchOutlined />, label: link("/documents", "Documents") },
      ];
  if (!admin && canModel) {
    items.push({ key: "/assistant", icon: <RobotOutlined />, label: link("/assistant", "Assistant") });
  }
  if (!admin && canAnalysis) {
    items.push({
      key: "/analytics",
      icon: <BarChartOutlined />,
      label: link("/analytics", "Analysis"),
    });
  }
  return items;
}

function Gated({
  ready,
  allowed,
  title,
  message,
  children,
}: {
  ready: boolean;
  allowed: boolean;
  title: string;
  message: string;
  children: ReactNode;
}) {
  if (!ready) {
    return <Card loading />;
  }
  if (!allowed) {
    return <Alert type="warning" showIcon message={title} description={message} />;
  }
  return children;
}

function Denied({ title, message }: { title: string; message: string }) {
  return <Alert type="warning" showIcon message={title} description={message} />;
}
