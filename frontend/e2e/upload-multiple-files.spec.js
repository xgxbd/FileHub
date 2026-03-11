import { expect, test } from '@playwright/test';

function buildUser() {
  const suffix = Date.now();
  return {
    username: `upload_multi_${suffix}`,
    email: `upload_multi_${suffix}@test.com`,
    password: 'Passw0rd!'
  };
}

test('上传页支持多文件选择并按队列完成上传', async ({ page }) => {
  const user = buildUser();

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(user.email);
  await page.getByPlaceholder('请输入用户名').fill(user.username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(user.password);
  await page.getByRole('button', { name: '注册并登录' }).click();
  await page.waitForURL('**/files');

  await page.goto('/upload?folder=logs');
  await expect(page.getByText('目标目录：/logs/')).toBeVisible();

  await page.setInputFiles('input[type="file"]', [
    {
      name: 'alpha.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('alpha-file')
    },
    {
      name: 'beta.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('beta-file')
    }
  ]);

  await expect(page.getByText('已选择 2 个文件')).toBeVisible();
  await page.getByRole('button', { name: '开始上传' }).click();
  await expect(page.getByText('已完成 2 个文件上传')).toBeVisible();

  await page.goto('/files');
  await page.locator('.folder-tree-panel .p-tree-node-content').filter({ hasText: 'logs' }).click();
  await expect(page.locator('tbody tr').filter({ hasText: 'alpha.txt' })).toHaveCount(1);
  await expect(page.locator('tbody tr').filter({ hasText: 'beta.txt' })).toHaveCount(1);
});
