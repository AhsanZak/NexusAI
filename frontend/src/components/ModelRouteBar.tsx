import { ReloadOutlined } from "@ant-design/icons";
import { Alert, Button, Select, Space, Tag, Typography } from "antd";
import { useState } from "react";

import { useChatModel } from "../chat/models";

export function ModelRouteBar() {
  const { models, modelId, choose, refresh } = useChatModel();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div>
      <Space align="center" wrap>
        <Typography.Text strong>Model</Typography.Text>
        <Select
          value={models.some((item) => item.id === modelId) ? modelId : undefined}
          placeholder="Choose a model"
          style={{ minWidth: 180 }}
          onChange={(value: string) => {
            void choose(value).catch((reason: unknown) => {
              setError(reason instanceof Error ? reason.message : "The model could not be changed");
            });
          }}
          options={models.map((item) => ({ value: item.id, label: item.name }))}
        />
        <Button
          icon={<ReloadOutlined />}
          loading={loading}
          onClick={() => {
            setLoading(true);
            void refresh()
              .catch((reason: unknown) => {
                setError(reason instanceof Error ? reason.message : "Models could not be loaded");
              })
              .finally(() => setLoading(false));
          }}
        >
          Refresh
        </Button>
      </Space>
      {error ? <Alert type="error" showIcon message={error} style={{ marginTop: 12 }} /> : null}
      <Space wrap style={{ marginTop: 8 }}>
        {models.map((item) => (
          <Tag key={item.id} color={item.state === "up" ? "success" : "error"}>
            {item.name}: {item.state === "up" ? "Working" : "Not working"}
          </Tag>
        ))}
      </Space>
    </div>
  );
}
