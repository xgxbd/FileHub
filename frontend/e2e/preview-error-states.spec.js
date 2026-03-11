import { expect, test } from '@playwright/test';

test('预览页能区分不支持预览与文件不存在', async ({ page }) => {
  const suffix = Date.now();
  const username = `preview_error_${suffix}`;
  const email = `${username}@test.com`;
  const password = 'Passw0rd!';
  const fileName = `preview-error-${suffix}.zip`;

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(email);
  await page.getByPlaceholder('请输入用户名').fill(username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(password);
  await page.getByRole('button', { name: '注册并登录' }).click();
  await page.waitForURL('**/files');

  await page.goto('/upload');
  await page.locator('input[type="file"]').setInputFiles({
    name: fileName,
    mimeType: 'application/zip',
    buffer: Buffer.from('PK\x03\x04zip-preview')
  });
  await page.getByRole('button', { name: '开始上传' }).click();
  await expect(page.getByText(`上传完成：${fileName}`)).toBeVisible();

  await page.goto('/files');
  const row = page.locator('tr', { hasText: fileName }).first();
  await expect(row).toBeVisible();
  await row.getByRole('button', { name: '预览' }).click();
  await expect(page.getByText('当前文件类型不支持在线预览')).toBeVisible();

  await page.goto('/preview/999999?name=ghost.txt');
  await expect(page.getByText('文件不存在')).toBeVisible();
});
