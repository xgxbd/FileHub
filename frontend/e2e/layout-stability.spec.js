import { expect, test } from '@playwright/test';

function buildUser() {
  const suffix = Date.now();
  return {
    username: `layout_user_${suffix}`,
    email: `layout_user_${suffix}@test.com`,
    password: 'Passw0rd!'
  };
}

test('方案D关键页面标题区高度保持稳定', async ({ page }) => {
  const user = buildUser();

  await page.goto('/register');
  await page.getByPlaceholder('请输入邮箱').fill(user.email);
  await page.getByPlaceholder('请输入用户名').fill(user.username);
  await page.getByPlaceholder('请输入密码（至少8位）').fill(user.password);
  await page.getByRole('button', { name: '注册并登录' }).click();
  await page.waitForURL('**/files');

  const routes = ['/files', '/upload', '/preview', '/recycle'];
  const heights = [];

  for (const route of routes) {
    await page.goto(route);
    await page.waitForLoadState('networkidle');

    const measured = await page.evaluate(() => {
      const topbar = document.querySelector('.topbar');
      const caption = document.querySelector('.p-card .p-card-caption');
      return {
        topbarHeight: topbar ? Math.round(topbar.getBoundingClientRect().height) : 0,
        captionHeight: caption ? Math.round(caption.getBoundingClientRect().height) : 0
      };
    });

    heights.push({ route, ...measured });
  }

  const topbarBase = heights[0].topbarHeight;
  const captionBase = heights[0].captionHeight;

  for (const item of heights) {
    expect(Math.abs(item.topbarHeight - topbarBase), `${item.route} topbar 高度异常`).toBeLessThanOrEqual(1);
    expect(Math.abs(item.captionHeight - captionBase), `${item.route} 标题区高度异常`).toBeLessThanOrEqual(1);
  }
});
