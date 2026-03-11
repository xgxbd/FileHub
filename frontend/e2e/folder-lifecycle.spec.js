import { expect, test } from '@playwright/test';

function buildUser() {
  const suffix = Date.now();
  return {
    username: `folder_life_${suffix}`,
    email: `folder_life_${suffix}@test.com`,
    password: 'Passw0rd!'
  };
}

test('文件夹支持重命名、递归删除并在回收站恢复', async ({ page }) => {
  const user = buildUser();

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(user.email);
  await page.getByPlaceholder('请输入用户名').fill(user.username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(user.password);
  await page.getByRole('button', { name: '注册并登录' }).click();
  await page.waitForURL('**/files');

  page.once('dialog', (dialog) => dialog.accept('logs'));
  await page.getByRole('button', { name: '新建文件夹' }).click();
  await expect(page.getByText('当前目录：/logs/')).toBeVisible();

  await page.evaluate(async () => {
    const token = window.localStorage.getItem('filehub_access_token');
    const content = 'readme';

    const createResp = await fetch('/api/upload/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        file_name: 'logs/readme.txt',
        total_size: content.length,
        chunk_size: 1024 * 1024,
        total_chunks: 1,
        mime_type: 'text/plain'
      })
    });
    const createData = await createResp.json();
    const form = new FormData();
    form.append('chunk', new Blob([content], { type: 'application/octet-stream' }), 'chunk.part');

    await fetch(`/api/upload/sessions/${createData.upload_id}/chunks/0`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}` },
      body: form
    });

    await fetch(`/api/upload/sessions/${createData.upload_id}/complete`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
  });

  page.once('dialog', (dialog) => dialog.accept('reports'));
  await page.getByRole('button', { name: '重命名' }).click();
  await expect(page.getByText('当前目录：/reports/')).toBeVisible();
  await expect(page.locator('tbody tr').first()).toContainText('readme.txt');
  await expect(page.locator('tbody tr').first()).toContainText('/reports/');

  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: '删除当前文件夹' }).click();
  await expect(page.getByText('当前目录：/')).toBeVisible();
  await expect(page.locator('.folder-tree-panel .p-tree-node-content').filter({ hasText: 'reports' })).toHaveCount(0);

  await page.goto('/recycle');
  await expect(page.locator('tbody tr').filter({ hasText: 'readme.txt' }).first()).toContainText('/reports/');
  await expect(page.getByRole('button', { name: '恢复文件夹' })).toBeVisible();
  await page.getByRole('button', { name: '恢复文件夹' }).click();
  await expect(page.getByText('已恢复文件夹：/reports/')).toBeVisible();

  await page.goto('/files');
  await page.getByRole('button', { name: '刷新' }).click();
  await page.locator('.folder-tree-panel .p-tree-node-content').filter({ hasText: 'reports' }).click();
  await expect(page.getByText('当前目录：/reports/')).toBeVisible();
  await expect(page.locator('tbody tr').first()).toContainText('readme.txt');
  await expect(page.locator('tbody tr').first()).toContainText('/reports/');
});
