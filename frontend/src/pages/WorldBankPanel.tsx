import { Alert, Card, Col, Row, Select, Statistic, Table, Typography } from "antd";
import type { TableColumnsType } from "antd";
import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import {
  loadWorldBankDashboard,
  type WorldBankDashboard,
  type WorldBankDocument,
} from "../api/worldbank";

const colors = ["#1f4b99", "#c2410c", "#0f766e", "#7c3aed", "#b45309", "#be123c", "#0369a1", "#3f6212"];

export function WorldBankPanel() {
  const [dashboard, setDashboard] = useState<WorldBankDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [indicator, setIndicator] = useState("NY.GDP.MKTP.CD");

  useEffect(() => {
    let active = true;
    loadWorldBankDashboard()
      .then((result) => {
        if (!active) {
          return;
        }
        setDashboard(result);
        setIndicator((current) => {
          if (result.indicators.some((item) => item.code === current)) {
            return current;
          }
          return result.indicators[0]?.code ?? current;
        });
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "World Bank data is unavailable");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const chart = useMemo(() => buildChart(dashboard, indicator), [dashboard, indicator]);

  if (error) {
    return <Alert type="error" showIcon message="World Bank warehouse is unavailable" description={error} />;
  }
  if (!dashboard) {
    return <Card loading />;
  }
  if (dashboard.observation_count === 0) {
    return (
      <Alert
        type="info"
        showIcon
        message="World Bank data is not loaded"
        description="Run the ingestion command against PostgreSQL. The indicators and documents come from the public World Bank APIs."
      />
    );
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card>
            <Statistic title="Indicator observations" value={dashboard.observation_count} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic title="Public reports" value={dashboard.document_count} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card>
            <Statistic title="Countries in this view" value={chart.countries.length} />
          </Card>
        </Col>
      </Row>
      <Card
        title="Country comparison"
        style={{ marginTop: 16 }}
        extra={
          <Select
            value={indicator}
            style={{ minWidth: 280 }}
            onChange={setIndicator}
            options={dashboard.indicators.map((item) => ({ value: item.code, label: item.name }))}
          />
        }
      >
        <Typography.Paragraph type="secondary">{scaleLabel(indicator)}</Typography.Paragraph>
        <div style={{ width: "100%", height: 360 }}>
          <ResponsiveContainer>
            <LineChart data={chart.rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Legend />
              {chart.countries.map((country, index) => (
                <Line
                  key={country}
                  type="monotone"
                  dataKey={country}
                  stroke={colors[index % colors.length]}
                  dot={false}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Card title="World Bank documents and reports" style={{ marginTop: 16 }}>
        <Table<WorldBankDocument>
          rowKey="id"
          columns={documentColumns}
          dataSource={dashboard.documents}
          pagination={false}
          scroll={{ x: 720 }}
        />
      </Card>
      <Typography.Paragraph type="secondary" style={{ marginTop: 16 }}>
        {dashboard.attribution} Retrieved {dashboard.retrieved_at ?? "unknown"}. Sources:{" "}
        <a href={dashboard.indicator_source}>{dashboard.indicator_source}</a>
        {" and "}
        <a href={dashboard.document_source}>{dashboard.document_source}</a>.
      </Typography.Paragraph>
    </div>
  );
}

const documentColumns: TableColumnsType<WorldBankDocument> = [
  { title: "Date", dataIndex: "document_date", width: 120 },
  {
    title: "Title",
    dataIndex: "title",
    render: (title: string, record) =>
      record.url ? (
        <a href={record.url} target="_blank" rel="noreferrer">
          {title}
        </a>
      ) : (
        title
      ),
  },
  { title: "Type", dataIndex: "doc_type", width: 220 },
];

function scaleLabel(indicator: string): string {
  if (indicator === "SP.POP.TOTL") {
    return "Population, millions of people.";
  }
  if (indicator === "FP.CPI.TOTL.ZG" || indicator === "SL.EMP.TOTL.SP.ZS") {
    return "Percent.";
  }
  return "Current US dollars, billions.";
}

function scaleValue(indicator: string, value: number): number {
  if (indicator === "SP.POP.TOTL") {
    return Number((value / 1_000_000).toFixed(2));
  }
  if (indicator === "FP.CPI.TOTL.ZG" || indicator === "SL.EMP.TOTL.SP.ZS") {
    return Number(value.toFixed(2));
  }
  return Number((value / 1_000_000_000).toFixed(2));
}

function buildChart(dashboard: WorldBankDashboard | null, indicator: string) {
  const chosen = dashboard?.series.filter((series) => series.indicator_code === indicator) ?? [];
  const byYear = new Map<number, Record<string, number | string>>();
  const countries: string[] = [];
  for (const series of chosen) {
    if (!countries.includes(series.country_name)) {
      countries.push(series.country_name);
    }
    for (const point of series.points) {
      const row = byYear.get(point.year) ?? { year: point.year };
      row[series.country_name] = scaleValue(indicator, point.value);
      byYear.set(point.year, row);
    }
  }
  return {
    countries,
    rows: [...byYear.values()].sort((left, right) => Number(left.year) - Number(right.year)),
  };
}
