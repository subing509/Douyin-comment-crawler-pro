抖音评论采集助手 — 使用说明与结构概览一、准备环境
1. 建议在独立虚拟环境中执行 `pipinstall-r requirements. txt` 安装 Playwright、pandas
等依赖。
2. 首次运行前执行 `playwright install chromium` 安装浏览器内核。
3. 如需代理或自定义 Chrome 路径，可在 `config. json`中调整 `proxy`、`proxy_list`、`chrome_path`
等字段。
二、运行步骤
1. 扫码登录：运行 `python main. py
--login`，浏览器自动打开抖音首页，扫码完成后关闭窗口即可保存Cookie。
2. 准备任务：在 `urls. txt` 中粘贴视频链接，支持`/video/{id}` 或 `jingxuan?modal_id={id
}`，程序会自动转换为标准播放页。
3. 启动采集：执行 `python main. py` 或 `python main. py --url
<单个链接>`，系统会逐条检查链接、建立浏览器上下文并加载评论区。
4. 查看结果：成功后在 `outputs/`  目录生成 `video_{视
频ID}_ {时间戳}. xlsx`，表格内含评论文本、用户昵称、点赞数、IP属地和视频元信息。
三、实用技巧
- 增量模式：在 `config. json` 打开
`enable_incremental`，即可只导出新增评论。
- 代理轮换：配置 `proxy_list` 并开启
`enable_proxy`，任务失败时会自动切换下一条代理。
- 断点续爬：通过 `resume_state_file`
记录进度，重复运行时会跳过已完成的链接。
四、程序结构总览
- `main. py`：命令入口，负责解析参数、加载配置、调用任务管理器。
- `config. json`：运行参数模板，集中管理最大评论数、滚动节奏、代理设置等。
- `urls. txt`：批量任务列表，每行一个视频链接。
- `src/services/`：浏览器控制、采集流程、数据导出、反检测等核心服务组件。
- `src/managers/`：任务调度、配置管理、错误处理与状态上报。

-
`requirements. txt`：依赖声明，方便客户在新环境快速安装。
五、常见问题
1. 无评论输出：确认链接为视频页或
`modal_id`，程序会自动规范化；若仍失败，可查看同目录下生成的`debug_no_comments_*. html`。
2. 登录失效：重新运行 `python main. py
--login`，或删除 `douyin_profile` 重新建库。
3. 触发验证码/限流：系统会自动等待并提示，可适当降低`max_comments` 或增加代理池。
