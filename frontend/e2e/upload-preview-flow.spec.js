import { expect, test } from '@playwright/test';

function buildUser() {
  const suffix = Date.now();
  return {
    username: `upload_preview_${suffix}`,
    email: `upload_preview_${suffix}@test.com`,
    password: 'Passw0rd!'
  };
}

test('上传页使用只读目标目录并可在预览页查看文本内容', async ({ page }) => {
  const user = buildUser();

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(user.email);
  await page.getByPlaceholder('请输入用户名').fill(user.username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(user.password);
  await page.getByRole('button', { name: '注册并登录' }).click();
  await page.waitForURL('**/files');

  await page.goto('/upload?folder=logs');
  await expect(page.getByText('目标目录：/logs/')).toBeVisible();
  await expect(page.getByText('目标文件夹（可选）')).toHaveCount(0);

  await page.setInputFiles('input[type=\"file\"]', {
    name: 'readme.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('preview flow text')
  });
  await page.getByRole('button', { name: '开始上传' }).click();
  await expect(page.getByText('上传完成：logs/readme.txt')).toBeVisible();

  await page.goto('/files');
  const logsTreeNode = page.locator('.folder-tree-panel .p-tree-node-content').filter({ hasText: 'logs' });
  await logsTreeNode.click();
  const debugFile = await page.evaluate(async () => {
    const token = window.localStorage.getItem('filehub_access_token');
    const listResp = await fetch('/api/files?page=1&page_size=20&directory=logs', {
      headers: { Authorization: `Bearer ${token}` }
    });
    const listData = await listResp.json();
    const first = listData.items[0];
    const previewResp = await fetch(`/api/files/${first.id}/preview`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return {
      listStatus: listResp.status,
      previewStatus: previewResp.status,
      fileName: first.file_name,
      size: first.size_bytes,
      mimeType: first.mime_type,
      previewLength: (await previewResp.text()).length
    };
  });
  expect(debugFile.listStatus).toBe(200);
  expect(debugFile.previewStatus).toBe(200);
  expect(debugFile.previewLength).toBeGreaterThan(0);
  await page.getByRole('button', { name: '预览' }).first().click();

  await expect(page.getByText('preview flow text')).toBeVisible();
  await expect(page.getByText('文件数')).toBeVisible();
  await expect(page.locator('.preview-layout .meta .row b').filter({ hasText: 'readme.txt' })).toBeVisible();
});
