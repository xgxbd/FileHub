(() => {
  const page = window.__PAGE_KEY__ || "files";
  const scheme = window.__SCHEME__ || "a";

  const pageMeta = {
    login: { title: "登录页", subtitle: "账号登录与注册入口" },
    files: { title: "文件仓库首页 / 文件列表", subtitle: "文件检索、筛选、批量操作" },
    upload: { title: "文件上传页", subtitle: "分片上传、队列、断点续传" },
    preview: { title: "文件详情 / 预览页", subtitle: "文件内容预览与元数据" },
    trash: { title: "回收站页", subtitle: "恢复与彻底删除" },
    admin: { title: "后台管理页", subtitle: "容量、活跃、系统健康" },
    logs: { title: "操作日志页", subtitle: "审计筛选与行为追踪" }
  };

  const navItems = [
    ["login", "登录"],
    ["files", "文件列表"],
    ["upload", "上传"],
    ["preview", "预览"],
    ["trash", "回收站"],
    ["admin", "后台"],
    ["logs", "日志"]
  ];

  const content = {
    login: {
      kpis: ["安全登录", "JWT 会话", "双角色"],
      primary: `
        <section class="panel login-panel">
          <div class="intro">
            <h2>文件仓库系统</h2>
            <p>专注文件上传、管理、预览、回收与审计。</p>
            <div class="chips">
              <span>分片上传</span><span>断点续传</span><span>操作留痕</span>
            </div>
          </div>
          <form class="form">
            <label>账号</label>
            <input value="demo_user" />
            <label>密码</label>
            <input type="password" value="******" />
            <label>验证码（可选）</label>
            <input value="A9KD" />
            <div class="actions">
              <button class="btn primary" type="button">登录</button>
              <button class="btn" type="button">注册</button>
            </div>
          </form>
        </section>
      `,
      side: `
        <section class="panel side-panel">
          <h3>登录安全提示</h3>
          <ul>
            <li>密码最少 8 位</li>
            <li>连续失败将触发临时锁定</li>
            <li>管理员登录全量审计</li>
          </ul>
        </section>
      `
    },
    files: {
      kpis: ["12,420 文件", "4.7 TB", "286 今日上传", "99.9% 成功率"],
      primary: `
        <section class="panel">
          <div class="toolbar">
            <button class="btn primary">上传文件</button>
            <button class="btn">新建目录</button>
            <button class="btn">批量下载</button>
            <button class="btn">筛选：本周</button>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>文件名</th><th>类型</th><th>大小</th><th>更新时间</th><th>状态</th></tr></thead>
              <tbody>
                <tr><td>产品路线图.pdf</td><td>PDF</td><td>24 MB</td><td>03-10 14:18</td><td><span class="tag ok">可预览</span></td></tr>
                <tr><td>release_20260310.zip</td><td>ZIP</td><td>2.1 GB</td><td>03-10 13:45</td><td><span class="tag warn">分片中</span></td></tr>
                <tr><td>接口压测记录.txt</td><td>TXT</td><td>64 KB</td><td>03-10 11:52</td><td><span class="tag ok">可预览</span></td></tr>
              </tbody>
            </table>
          </div>
        </section>
      `,
      side: `
        <section class="panel side-panel">
          <h3>最近任务</h3>
          <div class="task">video.mov <b>73%</b></div>
          <div class="task">archive.tar <b>41%</b></div>
          <h3>快捷筛选</h3>
          <div class="chips"><span>图片</span><span>PDF</span><span>压缩包</span></div>
        </section>
      `
    },
    upload: {
      kpis: ["队列 12", "并行 4", "失败重试 1"],
      primary: `
        <section class="panel upload-layout">
          <div class="dropzone">拖拽文件到此处或点击上传</div>
          <div class="queue">
            <div class="item">release.tar · 41%<div class="bar"><span style="width:41%"></span></div></div>
            <div class="item">video.mov · 73%<div class="bar"><span style="width:73%"></span></div></div>
            <div class="item">report.pdf · 100%<div class="bar"><span style="width:100%"></span></div></div>
            <div class="actions"><button class="btn primary">开始上传</button><button class="btn">暂停全部</button></div>
          </div>
        </section>
      `,
      side: `
        <section class="panel side-panel">
          <h3>上传策略</h3>
          <ul>
            <li>分片大小：8 MB</li>
            <li>并发上传：4</li>
            <li>失败重试：3 次</li>
          </ul>
        </section>
      `
    },
    preview: {
      kpis: ["PDF 预览", "内容检索", "下载统计"],
      primary: `
        <section class="panel preview-layout">
          <div class="preview-box">文件预览区域（图片 / PDF / TXT）</div>
          <div class="meta">
            <div class="row"><span>文件名</span><b>产品路线图.pdf</b></div>
            <div class="row"><span>上传者</span><b>王晨</b></div>
            <div class="row"><span>上传时间</span><b>03-10 14:18</b></div>
            <div class="row"><span>Hash</span><b>8db7...21ac</b></div>
            <div class="actions"><button class="btn primary">下载</button><button class="btn">移入回收站</button></div>
          </div>
        </section>
      `,
      side: `
        <section class="panel side-panel">
          <h3>相关文件</h3>
          <div class="task">发布说明_v2.pdf</div>
          <div class="task">需求变更记录.txt</div>
          <h3>统计</h3>
          <div class="task">最近 7 天下载：193</div>
        </section>
      `
    },
    trash: {
      kpis: ["129 回收文件", "9 即将到期", "30 天保留"],
      primary: `
        <section class="panel">
          <div class="toolbar">
            <button class="btn">仅看我删除</button>
            <button class="btn">最近 30 天</button>
            <button class="btn primary">恢复所选</button>
            <button class="btn">彻底删除</button>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>文件</th><th>原目录</th><th>删除时间</th><th>剩余保留</th><th>操作</th></tr></thead>
              <tbody>
                <tr><td>旧版方案.pptx</td><td>/项目文档</td><td>03-09 10:22</td><td>27 天</td><td><span class="tag warn">可恢复</span></td></tr>
                <tr><td>临时素材.ai</td><td>/设计稿</td><td>03-01 09:10</td><td>19 天</td><td><span class="tag bad">即将清理</span></td></tr>
              </tbody>
            </table>
          </div>
        </section>
      `,
      side: `
        <section class="panel side-panel">
          <h3>回收规则</h3>
          <ul>
            <li>默认保留 30 天</li>
            <li>到期自动清理</li>
            <li>管理员可提前删除</li>
          </ul>
        </section>
      `
    },
    admin: {
      kpis: ["活跃用户 324", "平均响应 83ms", "失败率 0.2%", "存储健康 良好"],
      primary: `
        <section class="panel chart-grid">
          <div class="chart"><h3>上传趋势（7 天）</h3><div class="bars"><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
          <div class="chart"><h3>用户活跃分布</h3><div class="bars"><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
        </section>
      `,
      side: `
        <section class="panel side-panel">
          <h3>管理动作</h3>
          <div class="actions stack"><button class="btn">用户管理</button><button class="btn">存储策略</button><button class="btn primary">导出报表</button></div>
        </section>
      `
    },
    logs: {
      kpis: ["今日日志 2,431", "异常 3", "高风险 1"],
      primary: `
        <section class="panel">
          <div class="toolbar">
            <button class="btn">用户：全部</button>
            <button class="btn">操作：上传/下载/删除</button>
            <button class="btn">时间：今天</button>
            <button class="btn primary">查询</button>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>时间</th><th>用户</th><th>操作</th><th>对象</th><th>结果</th><th>IP</th></tr></thead>
              <tbody>
                <tr><td>15:21:10</td><td>zhangsan</td><td>上传分片</td><td>asset.zip</td><td><span class="tag ok">成功</span></td><td>10.2.1.24</td></tr>
                <tr><td>15:18:47</td><td>admin</td><td>恢复文件</td><td>old.pptx</td><td><span class="tag ok">成功</span></td><td>10.2.1.10</td></tr>
                <tr><td>15:16:22</td><td>wangwu</td><td>彻底删除</td><td>tmp.ai</td><td><span class="tag bad">失败</span></td><td>10.2.1.48</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      `,
      side: `
        <section class="panel side-panel">
          <h3>实时流</h3>
          <div class="timeline"><div>15:22 分片合并完成</div><div>15:20 断点下载恢复</div><div>15:18 回收站恢复</div><div>15:16 登录成功</div></div>
        </section>
      `
    }
  };

  const meta = pageMeta[page] || pageMeta.files;
  const body = document.body;
  body.classList.add(`scheme-${scheme}`, `page-${page}`);

  const navHTML = navItems
    .map(([key, label]) => `<a class="nav-item ${page === key ? "active" : ""}" href="./${key}.html">${label}</a>`)
    .join("");

  const kpiHTML = (content[page].kpis || []).map((k) => `<div class="kpi">${k}</div>`).join("");

  document.getElementById("app").innerHTML = `
    <header class="topbar">
      <div class="brand">FileHub</div>
      <div class="page-info"><h1>${meta.title}</h1><p>${meta.subtitle}</p></div>
      <div class="top-actions"><button class="btn">全局搜索</button><button class="btn">管理员</button></div>
    </header>
    <div class="shell">
      <aside class="sidebar">${navHTML}</aside>
      <main class="main">
        <section class="kpi-row">${kpiHTML}</section>
        <section class="content-layout">
          <div class="primary">${content[page].primary}</div>
          <div class="secondary">${content[page].side}</div>
        </section>
      </main>
    </div>
  `;
})();
