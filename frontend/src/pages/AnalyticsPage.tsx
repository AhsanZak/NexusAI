import { Alert, Card, Col, Row, Statistic, Table, Typography } from "antd";
import type { TableColumnsType } from "antd";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { loadOlistDashboard, type OlistCategory, type OlistDashboard, type OlistPayment } from "../api/olist";

export function AnalyticsPage() {
  const [dashboard, setDashboard] = useState<OlistDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    loadOlistDashboard()
      .then((result) => {
        if (active) {
          setDashboard(result);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "Olist data is unavailable");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return <Alert type="error" showIcon message="Olist warehouse is unavailable" description={error} />;
  }
  if (!dashboard) {
    return <Card loading />;
  }
  if (dashboard.counts.orders === 0) {
    return (
      <Alert
        type="info"
        showIcon
        message="Olist data is not loaded"
        description="Run python -m app.ingestion.olist. It downloads the public Kaggle snapshot with kagglehub and loads the nine CSV files."
      />
    );
  }

  return (
    <div>
      <Typography.Title level={3}>Olist sales analytics</Typography.Title>
      <Typography.Paragraph>
        Brazilian e-commerce orders from 2016 to 2018. Prices are Brazilian reais from the published
        Olist snapshot, not a live store.
      </Typography.Paragraph>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title="Orders" value={dashboard.counts.orders} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title="Customers" value={dashboard.counts.customers} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title="Average review" value={dashboard.review_summary.average_score} precision={2} />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title="On-time delivery" suffix="%" value={dashboard.delivery.on_time_percent} />
          </Card>
        </Col>
      </Row>
      <Card title="Monthly item revenue" style={{ marginTop: 16 }}>
        <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={dashboard.monthly_sales}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="revenue" fill="#1f4b99" name="Revenue (BRL)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="Top categories by revenue">
            <Table<OlistCategory>
              rowKey="category"
              pagination={false}
              columns={categoryColumns}
              dataSource={dashboard.categories}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="Review scores">
            <div style={{ width: "100%", height: 280 }}>
              <ResponsiveContainer>
                <BarChart data={dashboard.review_scores}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="score" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="reviews" fill="#0f766e" name="Reviews" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
              {dashboard.review_summary.with_comment.toLocaleString()} of{" "}
              {dashboard.review_summary.reviews.toLocaleString()} reviews include a written comment.
            </Typography.Paragraph>
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="Delivery">
            <Typography.Paragraph>
              {dashboard.delivery.on_time.toLocaleString()} delivered on or before the estimate.{" "}
              {dashboard.delivery.late.toLocaleString()} arrived later. Average time from purchase to
              delivery is {dashboard.delivery.average_days} days.
            </Typography.Paragraph>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Payments">
            <Table<OlistPayment>
              rowKey="payment_type"
              pagination={false}
              columns={paymentColumns}
              dataSource={dashboard.payments}
            />
          </Card>
        </Col>
      </Row>
      <Typography.Paragraph type="secondary" style={{ marginTop: 16 }}>
        {dashboard.attribution}{" "}
        <a href={dashboard.source_url} target="_blank" rel="noreferrer">
          {dashboard.source_url}
        </a>
      </Typography.Paragraph>
    </div>
  );
}

const categoryColumns: TableColumnsType<OlistCategory> = [
  { title: "Category", dataIndex: "category" },
  { title: "Items", dataIndex: "items", width: 120 },
  {
    title: "Revenue (BRL)",
    dataIndex: "revenue",
    width: 160,
    render: (value: number) => value.toLocaleString(undefined, { maximumFractionDigits: 0 }),
  },
];

const paymentColumns: TableColumnsType<OlistPayment> = [
  { title: "Type", dataIndex: "payment_type" },
  { title: "Payments", dataIndex: "payments" },
  {
    title: "Amount (BRL)",
    dataIndex: "amount",
    render: (value: number) => value.toLocaleString(undefined, { maximumFractionDigits: 0 }),
  },
];
