import { expect, test } from '@playwright/test';

function buildUser() {
  const suffix = Date.now();
  return {
    username: `tree_sort_${suffix}`,
    email: `tree_sort_${suffix}@test.com`,
    password: 'Passw0rd!'
  };
}

test('文件列表页目录切换与排序切换即时生效', async ({ page }) => {
  const user = buildUser();

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(user.email);
  await page.getByPlaceholder('请输入用户名').fill(user.username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(user.password);
  await page.getByRole('button', { name: '注册并登录' }).click();
  await page.waitForURL('**/files');

  await page.evaluate(async () => {
    const token = window.localStorage.getItem('filehub_access_token');

    async function uploadVirtualFile(fileName, content) {
      const createResp = await fetch('/api/upload/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          file_name: fileName,
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
    }

    await uploadVirtualFile('alpha-root.txt', 'root file');
    await uploadVirtualFile('logs/zeta-log.txt', 'z log file');
    await uploadVirtualFile('logs/alpha-log.txt', 'a');
    await uploadVirtualFile('logs/big-log.txt', '12345678901234567890');
  });

  await page.goto('/files');
  await page.getByRole('button', { name: '刷新' }).click();

  const logsTreeNode = page.locator('.folder-tree-panel .p-tree-node-content').filter({ hasText: 'logs' });
  await expect(logsTreeNode).toBeVisible();

  await logsTreeNode.click();
  await expect(page.getByText('当前目录：/logs/')).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(3);

  await page.selectOption('.sort-select', 'file_name_asc');
  await expect(page.locator('tbody tr').first()).toContainText('logs/alpha-log.txt');

  await page.selectOption('.sort-select', 'size_desc');
  await expect(page.locator('tbody tr').first()).toContainText('logs/big-log.txt');

  await page.getByRole('button', { name: '根目录' }).click();
  await expect(page.getByText('当前目录：/')).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await expect(page.locator('tbody tr').first()).toContainText('alpha-root.txt');
});
