import { BugOutlined, SendOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Descriptions, Drawer, Input, Select, Space, Table, Tag, Typography } from "antd";
import type { TableColumnsType } from "antd";
import { useCallback, useEffect, useState } from "react";

import { loadGatewayStatus, loadTraces, sendDebugPrompt, type GatewayStatus, type LlmTrace } from "../api/debug";
import { ModelRouteBar } from "../components/ModelRouteBar";
import { useNarrow } from "../ui/useNarrow";

export function DebugPage() {
  const narrow = useNarrow();
  const [status, setStatus] = useState<GatewayStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [traces, setTraces] = useState<LlmTrace[]>([]);
  const [filter, setFilter] = useState("");
  const [prompt, setPrompt] = useState("");
  const [sending, setSending] = useState(false);
  const [selected, setSelected] = useState<LlmTrace | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [gateway, page] = await Promise.all([loadGatewayStatus(), loadTraces(filter)]);
      setStatus(gateway);
      setTraces(page.items);
      setStatusError(null);
    } catch (error) {
      setStatusError(error instanceof Error ? error.message : "Debug API is unavailable");
    }
  }, [filter]);

  useEffect(() => {
    let active = true;
    const run = () => {
      if (active) {
        void refresh();
      }
    };
    run();
    const timer = window.setInterval(run, 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [refresh]);

  async function onSend() {
    const text = prompt.trim();
    if (!text) {
      return;
    }
    setSending(true);
    try {
      const trace = await sendDebugPrompt(text);
      setSelected(trace);
      setPrompt("");
      await refresh();
    } catch (error) {
      setStatusError(error instanceof Error ? error.message : "The debug call failed");
    } finally {
      setSending(false);
    }
  }

  const columns: TableColumnsType<LlmTrace> = [
    {
      title: "When",
      dataIndex: "created_at",
      render: (value: string) => new Date(value).toLocaleString(),
      width: 190,
    },
    {
      title: "Status",
      dataIndex: "status",
      width: 110,
      render: (value: string) => <Tag color={value === "success" ? "success" : "error"}>{value}</Tag>,
    },
    { title: "Source", dataIndex: "source", width: 130 },
    { title: "Model", dataIndex: "model" },
    {
      title: "Latency",
      dataIndex: "latency_ms",
      width: 110,
      render: (value: number | null) => (value === null ? "—" : `${value.toFixed(0)} ms`),
    },
    {
      title: "Tokens",
      dataIndex: "total_tokens",
      width: 90,
      render: (value: number | null) => value ?? "—",
    },
  ];

  return (
    <div>
      <Typography.Title level={3}>
        <BugOutlined /> Model status
      </Typography.Title>
      <Typography.Paragraph>
        The label below is the route that answers chat. Green means that option responded to a
        status check. Red means it did not. Refresh runs the checks again. A test prompt uses only
        the route marked in use.
      </Typography.Paragraph>
      {statusError ? <Alert type="error" showIcon message={statusError} style={{ marginBottom: 16 }} /> : null}
      <Card style={{ marginBottom: 16 }}>
        <ModelRouteBar />
      </Card>

      <Card title="Gateway" style={{ marginBottom: 16 }}>
        <Descriptions column={{ xs: 1, sm: 2, md: 3 }} size="small">
          <Descriptions.Item label="Alias">{status?.model_alias ?? "—"}</Descriptions.Item>
          <Descriptions.Item label="Model">{status?.model ?? "—"}</Descriptions.Item>
          <Descriptions.Item label="In use">{status?.active_label ?? "—"}</Descriptions.Item>
          <Descriptions.Item label="API base">{status?.api_base || "api.openai.com"}</Descriptions.Item>
          <Descriptions.Item label="Configured">
            <Tag color={status?.configured ? "success" : "warning"}>{status?.configured ? "yes" : "no"}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Timeout">{status ? `${status.timeout_seconds}s` : "—"}</Descriptions.Item>
          <Descriptions.Item label="Retries">{status?.max_retries ?? "—"}</Descriptions.Item>
          <Descriptions.Item label="Trace store">{status?.trace_dialect ?? "—"}</Descriptions.Item>
          <Descriptions.Item label="Traces">{status?.trace_count ?? "—"}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Send a test prompt" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <Input.TextArea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            rows={4}
            placeholder="Ask a short question. It goes to the route marked in use."
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => void onSend()}
            loading={sending}
            disabled={!prompt.trim()}
          >
            Send through the active model
          </Button>
        </Space>
      </Card>

      <Card
        title="Call log"
        extra={
          <Select
            value={filter}
            style={{ width: 160 }}
            onChange={setFilter}
            options={[
              { value: "", label: "All calls" },
              { value: "success", label: "Success" },
              { value: "error", label: "Errors" },
            ]}
          />
        }
      >
        <Table<LlmTrace>
          rowKey="id"
          columns={columns}
          dataSource={traces}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 860 }}
          onRow={(record) => ({ onClick: () => setSelected(record) })}
        />
      </Card>

      <Drawer
        title="Trace detail"
        width={narrow ? "100%" : 640}
        open={selected !== null}
        onClose={() => setSelected(null)}
      >
        {selected ? <TraceDetail trace={selected} /> : null}
      </Drawer>
    </div>
  );
}

function TraceDetail({ trace }: { trace: LlmTrace }) {
  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="ID">{trace.id}</Descriptions.Item>
        <Descriptions.Item label="Provider response">{trace.provider_response_id ?? "—"}</Descriptions.Item>
        <Descriptions.Item label="Status">{trace.status}</Descriptions.Item>
        <Descriptions.Item label="Error type">{trace.error_type ?? "—"}</Descriptions.Item>
        <Descriptions.Item label="Prompt tokens">{trace.prompt_tokens ?? "—"}</Descriptions.Item>
        <Descriptions.Item label="Completion tokens">{trace.completion_tokens ?? "—"}</Descriptions.Item>
      </Descriptions>
      {trace.error_message ? (
        <Alert type="error" message="Error" description={trace.error_message} />
      ) : null}
      <div>
        <Typography.Text strong>Request</Typography.Text>
        <pre style={preStyle}>{JSON.stringify(trace.request_messages, null, 2)}</pre>
      </div>
      <div>
        <Typography.Text strong>Response</Typography.Text>
        <pre style={preStyle}>{trace.response_text ?? "No response text"}</pre>
      </div>
    </Space>
  );
}

const preStyle = {
  background: "#f6f8fa",
  padding: 12,
  overflow: "auto",
  whiteSpace: "pre-wrap" as const,
};
