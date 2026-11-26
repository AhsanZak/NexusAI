import { ReloadOutlined } from "@ant-design/icons";
import { Alert, Button, Select, Space, Tooltip } from "antd";
import { useState } from "react";

import litellmMark from "../assets/brands/litellm.svg";
import ollamaMark from "../assets/brands/ollama.svg";
import openaiMark from "../assets/brands/openai.svg";
import { useChatModel } from "../chat/models";

const MARKS: Record<string, string> = {
  "local-ollama": ollamaMark,
  "smart-ollama": ollamaMark,
  openai: openaiMark,
  litellm: litellmMark,
};

export function ModelRouteBar() {
  const { models, modelId, choose, refresh } = useChatModel();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div>
      <Space className="model-route" align="center" wrap>
        <Select
          value={models.some((item) => item.id === modelId) ? modelId : undefined}
          placeholder="Choose a model"
          popupMatchSelectWidth={false}
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
        {models.map((item) => {
          const up = item.state === "up";
          return (
            <Tooltip key={item.id} title={item.name}>
              <span aria-label={item.name} style={{ position: "relative", display: "inline-flex" }}>
                <img src={MARKS[item.id] ?? litellmMark} alt="" width={18} height={18} />
                <span
                  style={{
                    position: "absolute",
                    right: -3,
                    bottom: -2,
                    width: 7,
                    height: 7,
                    borderRadius: "50%",
                    background: up ? "#52c41a" : "#ff4d4f",
                    boxShadow: "0 0 0 1px #fff",
                  }}
                />
              </span>
            </Tooltip>
          );
        })}
      </Space>
      {error ? <Alert type="error" showIcon message={error} style={{ marginTop: 12 }} /> : null}
    </div>
  );
}
