import { expect, test } from '@playwright/test';

test('登录页可正常加载', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByText('登录 FileHub')).toBeVisible();
  await expect(page.getByRole('button', { name: '登录' })).toBeVisible();
});
