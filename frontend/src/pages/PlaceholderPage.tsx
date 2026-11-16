import { Card, Typography } from "antd";

interface PlaceholderPageProps {
  title: string;
  milestone: string;
}

export function PlaceholderPage({ title, milestone }: PlaceholderPageProps) {
  return (
    <Card>
      <Typography.Title level={3}>{title}</Typography.Title>
      <Typography.Paragraph>
        {milestone}. The navigation entry is here so the module map stays visible while that work
        is still ahead.
      </Typography.Paragraph>
    </Card>
  );
}
