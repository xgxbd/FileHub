import { expect, test } from '@playwright/test';

test('关键流程：注册登录上传下载删除恢复', async ({ page }) => {
  const suffix = Date.now();
  const username = `e2e_user_${suffix}`;
  const email = `${username}@test.com`;
  const password = 'Passw0rd!';
  const fileName = `e2e-${suffix}.txt`;

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(email);
  await page.getByPlaceholder('请输入用户名').fill(username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(password);
  await page.getByRole('button', { name: '注册并登录' }).click();

  await page.waitForURL('**/files');
  await expect(page.getByText('文件仓库首页')).toBeVisible();

  await page.locator('input[type="file"]').setInputFiles({
    name: fileName,
    mimeType: 'text/plain',
    buffer: Buffer.from(`hello-${suffix}`)
  });
  await page.getByRole('button', { name: '开始上传' }).click();

  await expect(page.getByText('上传完成')).toBeVisible({ timeout: 120000 });

  const row = page.locator('tr', { hasText: fileName }).first();
  await expect(row).toBeVisible({ timeout: 30000 });

  const downloadPromise = page.waitForEvent('download');
  await row.getByRole('button', { name: '下载' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe(fileName);

  page.once('dialog', (dialog) => dialog.accept());
  await row.getByRole('button', { name: '删除' }).click();
  await expect(page.locator('tr', { hasText: fileName })).toHaveCount(0, { timeout: 30000 });

  await page.getByRole('button', { name: '回收站' }).click();
  await page.waitForURL('**/recycle');

  const recycleRow = page.locator('tr', { hasText: fileName }).first();
  await expect(recycleRow).toBeVisible({ timeout: 30000 });
  await recycleRow.getByRole('button', { name: '恢复' }).click();
  await expect(page.getByText(`已恢复文件：${fileName}`)).toBeVisible({ timeout: 30000 });

  await page.getByRole('button', { name: '文件中心' }).click();
  await page.waitForURL('**/files');
  await expect(page.locator('tr', { hasText: fileName }).first()).toBeVisible({ timeout: 30000 });
});
