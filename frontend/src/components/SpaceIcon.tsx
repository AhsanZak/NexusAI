import {
  FileExcelOutlined,
  FilePdfOutlined,
  FileTextOutlined,
  LineChartOutlined,
  PictureOutlined,
  RobotOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";
import type { ReactNode } from "react";

const icons: Record<string, ReactNode> = {
  pdf: <FilePdfOutlined />,
  excel: <FileExcelOutlined />,
  image: <PictureOutlined />,
  graph: <LineChartOutlined />,
  video: <VideoCameraOutlined />,
  document: <FileTextOutlined />,
};

export function SpaceIcon({ space }: { space: string | null }) {
  if (!space) {
    return <RobotOutlined />;
  }
  return icons[space] ?? <FileTextOutlined />;
}
