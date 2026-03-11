import { expect, test } from '@playwright/test';

test('后端托管前端模式下可访问核心页面', async ({ page }) => {
  const suffix = Date.now();
  const username = `hosted_user_${suffix}`;
  const email = `${username}@test.com`;
  const password = 'Passw0rd!';

  await page.goto('/login');
  await expect(page.getByRole('heading', { name: '登录页' })).toBeVisible();

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(email);
  await page.getByPlaceholder('请输入用户名').fill(username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(password);
  await page.getByRole('button', { name: '注册并登录' }).click();

  await page.waitForURL('**/files');
  await expect(page.getByRole('heading', { name: '文件仓库首页 / 文件列表' })).toBeVisible();

  await page.goto('/upload');
  await expect(page.getByRole('heading', { name: '文件上传页' })).toBeVisible();

  await page.goto('/preview');
  await expect(page.getByRole('heading', { name: '文件详情 / 预览页' })).toBeVisible();

  await page.goto('/recycle');
  await expect(page.getByRole('heading', { name: '回收站页' })).toBeVisible();
});
