import { expect, test } from '@playwright/test';

function buildUser() {
  const suffix = Date.now();
  return {
    username: `folder_ui_${suffix}`,
    email: `folder_ui_${suffix}@test.com`,
    password: 'Passw0rd!'
  };
}

test('文件列表页支持创建与删除空文件夹', async ({ page }) => {
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

  page.once('dialog', (dialog) => dialog.accept('archive'));
  await page.getByRole('button', { name: '新建文件夹' }).click();
  await expect(page.getByText('当前目录：/logs/archive/')).toBeVisible();

  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: '删除当前文件夹' }).click();
  await expect(page.getByText('当前目录：/logs/')).toBeVisible();
  await expect(page.locator('.folder-tree-panel .p-tree-node-content').filter({ hasText: 'archive' })).toHaveCount(0);
});
