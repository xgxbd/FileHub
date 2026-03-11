import { expect, test } from '@playwright/test';

test('上传页支持停止队列并重试未完成文件', async ({ page }) => {
  const suffix = Date.now();
  const username = `upload_queue_${suffix}`;
  const email = `${username}@test.com`;
  const password = 'Passw0rd!';

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(email);
  await page.getByPlaceholder('请输入用户名').fill(username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(password);
  await page.getByRole('button', { name: '注册并登录' }).click();
  await page.waitForURL('**/files');

  const files = [
    {
      name: `queue-a-${suffix}.txt`,
      mimeType: 'text/plain',
      buffer: Buffer.alloc(6 * 1024 * 1024, 'a')
    },
    {
      name: `queue-b-${suffix}.txt`,
      mimeType: 'text/plain',
      buffer: Buffer.alloc(6 * 1024 * 1024, 'b')
    },
    {
      name: `queue-c-${suffix}.txt`,
      mimeType: 'text/plain',
      buffer: Buffer.alloc(6 * 1024 * 1024, 'c')
    }
  ];

  await page.goto('/upload');
  await page.locator('input[type="file"]').setInputFiles(files);
  await page.getByRole('button', { name: '开始上传' }).click();
  await page.getByRole('button', { name: '停止队列' }).click();

  await expect(page.getByText(/已停止剩余上传任务/)).toBeVisible({ timeout: 120000 });
  await expect(page.locator('.queue .item').filter({ hasText: '已取消' }).first()).toBeVisible();

  await page.getByRole('button', { name: '重试未完成' }).click();
  await expect(page.getByText(/已完成 [1-3] 个文件上传/)).toBeVisible({ timeout: 120000 });
  await expect(page.locator('.queue .item').filter({ hasText: '已完成' })).toHaveCount(3, { timeout: 120000 });
});
