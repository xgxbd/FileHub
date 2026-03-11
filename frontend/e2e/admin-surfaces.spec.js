import { expect, test } from '@playwright/test';

test('管理员可筛选文件并查看日志', async ({ page }) => {
  const suffix = Date.now();
  const username = `admin_surface_user_${suffix}`;
  const email = `${username}@test.com`;
  const password = 'Passw0rd!';
  const fileName = `admin-surface-${suffix}.txt`;

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(email);
  await page.getByPlaceholder('请输入用户名').fill(username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(password);
  await page.getByRole('button', { name: '注册并登录' }).click();
  await page.waitForURL('**/files');

  await page.goto('/upload?folder=logs');
  await page.locator('input[type="file"]').setInputFiles({
    name: fileName,
    mimeType: 'text/plain',
    buffer: Buffer.from(`admin-surface-${suffix}`)
  });
  await page.getByRole('button', { name: '开始上传' }).click();
  await expect(page.getByText(`上传完成：logs/${fileName}`)).toBeVisible();

  await page.getByRole('button', { name: '退出' }).click();
  await page.waitForURL('**/login');

  await page.getByPlaceholder('请输入邮箱或用户名').fill('admin');
  await page.getByPlaceholder('请输入密码').fill('ChangeMe123!');
  await page.getByRole('main').getByRole('button', { name: '登录' }).click();
  await page.waitForURL('**/files');

  await page.goto('/admin/files');
  await page.getByPlaceholder('例如：report、photo').fill(fileName);
  await page.getByRole('button', { name: '查询' }).click();

  const fileRow = page.locator('tr', { hasText: fileName }).first();
  await expect(fileRow).toBeVisible();
  await expect(fileRow.getByText('/logs/')).toBeVisible();

  page.once('dialog', (dialog) => dialog.accept());
  await fileRow.getByRole('button', { name: '删除' }).click();
  await expect(page.getByText(`已删除：${fileName}`)).toBeVisible();

  await page.getByRole('button', { name: '已删除文件' }).click();
  await page.getByRole('button', { name: '查询' }).click();
  const deletedRow = page.locator('tr', { hasText: fileName }).first();
  await expect(deletedRow).toBeVisible();
  await deletedRow.getByRole('button', { name: '恢复' }).click();
  await expect(page.getByText(`已恢复：${fileName}`)).toBeVisible();

  await page.goto('/admin/logs');
  await page.getByPlaceholder('例如：login、download').fill('soft_delete');
  await page.getByRole('button', { name: '查询' }).click();
  await expect(page.locator('tr', { hasText: 'soft_delete' }).first()).toBeVisible();
});
