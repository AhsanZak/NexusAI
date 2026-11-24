import { Card } from "antd";

import { PermissionAdmin } from "../components/PermissionAdmin";
import { UploadAdmin } from "../components/UploadAdmin";
import { UserAdmin } from "../components/UserAdmin";

export function AdminPage() {
  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <UserAdmin />
      </Card>
      <Card style={{ marginBottom: 16 }}>
        <PermissionAdmin />
      </Card>
      <Card>
        <UploadAdmin />
      </Card>
    </div>
  );
}
