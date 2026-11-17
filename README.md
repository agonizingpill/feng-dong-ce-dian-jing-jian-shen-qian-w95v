# 翼衡风研 · 风洞测点精简审签

用扫角记录评估压力测点贡献，在有限通道内保留三翼段覆盖并完成试验审签。

模拟客户：翼衡风研，20人低速风洞试验组，W-12翼模原有12个压力测点。过去工程师在纸图勾选测点，凭线性相关性剪掉低贡献点；经常超接线预算，未标定点误入布置，精简后翼尖失去覆盖。本项目承接测点标定与扫角压力/升力记录，替代贡献筛选和接线审查，下游是试验负责人签发的通道布置。

## 业务模块

- 翼面测点：Probe编号唯一、翼根/root、翼中/mid、翼尖/tip、弦向/展向位置、标定和启用状态。P12为未标定异常示例。
- 扫角台账：Sweep记录编号、风速、攻角与升力；每个压力值独立存Pressure(sweep_id,probe_id,pascal)，双外键与唯一约束，禁止缺码/未知码/超量程。
- 互信息排序：Python worker在96条训练样本内计算mutual_info_regression(seed42)，按预算自动选点，24条留出只评估回归误差；手动改点后重新回算。
- 测点校准证书：CalibrationCertificate关联测点，记录零点/跨度误差与有效期；工程师录草稿，负责人签发，超限或过期不得签，签发后不可覆盖。
- 风洞试验开车核对：TunnelRun只关联signed布置；开车前检查全部选点的最新签发证书、10–50m/s和−10至20°包线、三项安全联锁；负责人开车保存独立快照，工程师记录试验完结。
- 布置审签：Layout与Probe通过LayoutProbe双外键关联。负责人必须核对三翼段覆盖、全部标定/启用、通道不超预算和来源校验。超过预算不能保存，缺翼段或未标定不能审签，拒绝不改状态。

标定或扫角变更使未审签布置失效；有计算中的方案暂不能改来源。第一份方案审签后整个试验来源冻结，签后方案不能改点。证据含测点快照、选点真实ID、训练/验证记录编号及来源SHA256，避免已签方案受新输入影响。

## 快速启动

```sh
cp .env.example .env
docker compose config --quiet
docker compose up -d --build
docker compose exec -T backend python -m scripts.seed_demo
```

[工作台](http://localhost:18227)，[API文档](http://localhost:19227/docs)，MySQL映射17727。

|账号|口令|角色|任务|
|---|---|---|---|
|admin@yiheng.demo|Tunnel2026!|admin 试验负责人|全部操作、布置审签、校准证书签发和开车|
|engineer@yiheng.demo|Tunnel2026!|engineer 试验工程师|修订标定/扫角、计算、选点、证书草稿、试验计划/完结；不能签发或开车|
|viewer@yiheng.demo|Tunnel2026!|viewer 观察员|九业务页只读|

JWT8小时，PBKDF2-SHA256盐化密码；演示部署前修改JWT_SECRET及数据库口令。

## 一天的试验剧本

1. 08:30 工程师查看W-12翼模，P01–P04翼根、P05–P08翼中、P09–P12翼尖。
2. 09:00 核对12测点位置与标定，P12尚未完成标定，不能签入正式接线。
3. 09:30 复核SW-001至SW-120的风速18–42m/s、攻角−4至16°和12点压力。
4. 10:00 创建3通道布置，后台只在训练集计算贡献，查看精简与全测点留出误差。
5. 10:30 演练P01/P02/P05缺翼尖方案，负责人审签被拒。
6. 11:00 演练P01/P05/P12三翼段齐全但含未标定点，仍被拒；增加第4点超过预算时也拒绝保存。
7. 14:00 改成P01/P05/P09，worker重新计算实际选中集误差，再由负责人审签。
8. 16:00 观察员核对签发状态与来源校验；之后不能修改来源或已签选点。修改采样来源需要独立版本；复用已签布置的新开车另建试验核对单。

## 算法与可复现边界

输入是完整扫角压力矩阵X和升力y，至少40组。固定train_test_split(test_size=.2,random_state=42)得到96/24；互信息仅fit训练96条。按训练互信息降序选择max_channels，或采用工程师显式选择；StandardScaler+Ridge(alpha=1)只在训练拟合，再在24条留出上报告MAE，另算全12点基准MAE。没有先用全部数据选特征再拆验证的泄漏。手动反复改点时留出集会被重复查看，因此不将最终人工选择视为独立盲测性能。

Pressure与LayoutProbe是真实关系表，JSON只保存衍生计算证据。worker结果同时写Layout.evidence和共享卷`/artifacts/layout-<id>.json`。源码不硬编码计算排名或图表数据。数据由固定seed42生成，非真实客户风洞测量。

## 工程与本地开发

|层|实现|
|---|---|
|前端|原生HTML/CSS/JS ES modules、Nginx1.27|
|后端|Python3.12 FastAPI / SQLAlchemy / PyJWT|
|算法|scikit-learn1.6.1、NumPy、Redis worker|
|持久化|MySQL8、Redis7 AOF、共享计算卷|

五服务frontend/backend/worker/db/redis，全部健康检查。MySQL用TCP127.0.0.1业务账号SELECT1保证初始化完成；worker有心跳；Nginx/api去掉前缀代理。显式10.221.28.0/24子网可在.env调整；端口、COMPOSE_PROJECT_NAME、JWT_SECRET、SEED_DEMO见.env.example。数据库/Redis/共享产物分别命名卷。

`backend/src/models.py`领域表与双关联；`schemas.py`输入；`services.py`约束、来源失效和SHA；`selection.py`无泄漏选择/验证；`worker.py`队列；`main.py`权限路由；`auth.py`JWT；`middlewares.py`请求ID与限流。seed按自然键仅补缺失，不改用户资料。

`frontend/src/pages/probes.js`定位/标定、`sweeps.js`带12压力表单、`ranking.js`预算/贡献、`review.js`逐翼段选点/审签。`api.js`HTTP、`store.js`状态、`components/instruments.js`翼面图/状态/选择器、`utils/format.js`转义/数字/表单。角色、翼段、布局状态在backend/src/constants.py和frontend/src/constants.js；schemas.py含翼段Literal，selection.py使用实际ID关系。权限后端执行；IntegrityError转可恢复409。

本地安装backend/requirements.txt，设置DATABASE_URL/REDIS_URL，backend目录运行`uvicorn src.main:app --reload`，另一终端`python -m src.worker`；前端建议保留Compose Nginx代理。停止`docker compose down`，清数据`down -v --remove-orphans`。

已知范围：单翼模12测点、随机留出按独立扫角假设，实际时序漂移场景应按试验批次验证；签后整套来源冻结，没有多版本重开、撤签或采集硬件接口。worker崩溃作业自动重投未实现。Google字体离线回退。验收脚本/日志/截图在`../../test-artifacts/gb-1028/`。

## 校准与开车扩展

`calibration_models.py` 保存证书实体；`calibration_service.py` 校验零点绝对误差≤0.5Pa、跨度绝对误差≤1%，有效期不得早于Asia/Shanghai当前日期（有效至当日包含当天）。工程师可修改草稿，测点和编号固定；负责人签发后不可覆盖，新一次校准另建新证书。每个测点以最近 `issued_at` 的已签证书作为当前证书，过期不回退到较旧证书。

新证书独立于原Probe.calibrated与source_checksum，不修改已经冻结的标定布尔值、位置、压力源或已签Layout。旧布置保持原签署规则与历史证据；后续新开车必须另外通过当前证书检查。原“来源冻结”限制仍适用于Probe/Sweep编辑，不阻止登记独立新校准证书。

`run_models.py` 保存计划→运行→完结。计划可带未完成联锁或超开车包线值，负责人开车时再次拒绝；计划可修正，运行后不能改条件。开车包线10–50m/s、攻角−10至20°；风道清场、急停联锁测试、模型固定三项必须全部确认。开车在测点锁下读取每个选点当前已签且有效证书，保存完整Layout（含原evidence与来源SHA）、选点位置/状态、每张证书、速度/攻角/联锁和负责人时刻。换新证书不影响旧运行快照。完结记录至少8字设备收尾说明，不重新写入原扫角Pressure。

`readiness_schemas.py` 提供数值/日期/联锁请求模型，`readiness_routes.py` 负责独立事务与角色；前端 `pages/calibration.js` / `pages/runs.js` 两页通过store/api真实读写。证书状态和试验状态在前后端constants定义。

|接口|权限|
|---|---|
|GET /calibration-certificates、/tunnel-runs|三角色读取|
|POST /calibration-certificates、PUT /calibration-certificates/{id}|admin/engineer录入、修订草稿|
|POST /calibration-certificates/{id}/issue|仅admin签发|
|POST /tunnel-runs、PUT /tunnel-runs/{id}|admin/engineer编制和修正计划|
|POST /tunnel-runs/{id}/start|仅admin开车|
|POST /tunnel-runs/{id}/complete|admin/engineer完结|

seed另有P01/P05两张有效已签演示证书及P09一张过期证书（明确以seed:lab-archive标识历史演练签发人）；可用原布置P01/P05/P09演练过期拒开，再登记并签发P09新证书后开车。日期相对首次seed日期构造，重复seed不延长已有证书有效期、不覆盖人工修订/签发/试验快照。新增两张表使用create_all，原表无新增列或回填。

当前范围：校准测量及安全联锁由人员录入确认，不连接硬件；开车不控制真实风机，完结不自动采集新压力或升力；通道采集模块可人工录入实际压力序列。没有吊销/撤签、实际试验数据导入、自动停机、证书电子签章或多翼模版本。生产控制应由独立设备系统承担；本项目实现业务记录和约束。运行证据在 `test-artifacts/gb-1028/expansion/`。

MIT License。


## 装夹、采集与交付（三个追加模块 / v3）

现有六页保留，新增翼模装夹、通道采集、试验交付三页。主管负责装夹验收、采集冻结和交付核准；工程师可编制/关联装夹、录入采样、提交交付及登记回执，viewer九页只读。所有写权限与状态门槛由后端执行。

装夹 `ModelMount` 关联已signed布局，记录质量kg、迎风面积m²、固定扭矩N·m、核准载荷N。草稿可修订，编号和布局固定；主管只验收20–80N·m扭矩，验收后不可改。`RunMount` 对每个试验唯一，未开车时可更换为同布局已验收装夹。新开车除原证书/包线/联锁外，须有匹配装夹，并在事务锁下计算 `q=0.5×rho×speed²` Pa，气动载荷 `q×area` N，静重 `mass×g` N，合计不得超过核准载荷。固定rho=1.225kg/m³、g=9.80665m/s²，实际参数、公式、常数及三项载荷全部写入独立开车快照。此为小型低速工况的保守简化合载估计，没有升阻力系数、姿态分解或有限元结构校核，不替代真实结构验收。

`AcquisitionBatch` 每试验唯一，只有running可建立，频率1–1000Hz、时长1–60s且乘积≤20000。逐选点输入实际压力序列（每通道1–20000个有限数字、±10000Pa），`ChannelReading` 存完整数组、后端len得实样数、statistics.fmean得均压。保存会替换本批通道集合，允许先存部分通道，不接受外点或重复通道；仅试验运行且未冻结可写。主管冻结要求覆盖开车快照全部所选点，每通道实际数≥频率×时长。每通道缺失率=max(期望数−实样数,0)/期望数，批缺失率为所选通道缺失率均值，批均压为各通道均压的均值。冻结可在停风后复核，但采样写入必须在running时完成；冻结后不可覆盖或重复签署。

`TunnelDelivery` 每试验唯一，必须completed且有完整冻结采集、开车装夹快照。提交生成独立的试验/原布局/选点/证书/装夹/真实采样及汇总快照；submitted→主管approved→工程师登记≥8字回执acknowledged。不可先回执或重复发布/签收。本地留痕，没有外发、电子签章或真实客户认证。

|追加接口|权限与动作|
|---|---|
|GET /model-mounts、/run-mounts、/acquisition-batches、/tunnel-deliveries|三角色读取|
|POST /model-mounts、PUT /model-mounts/{id}|工程师/主管登记和修草稿|
|POST /model-mounts/{id}/accept|主管验收|
|POST /run-mounts、PUT /run-mounts/{run_id}|工程师/主管关联或修订计划装夹|
|POST /acquisition-batches、PUT /acquisition-batches/{id}/readings|工程师/主管建立批次、录实际序列|
|POST /acquisition-batches/{id}/freeze|主管完整性核验并冻结|
|POST /tunnel-deliveries、POST /tunnel-deliveries/{id}/acknowledge|工程师/主管提交、登记回执|
|POST /tunnel-deliveries/{id}/approve|主管核准发布|

追加源文件按职责组织：mount_models/acquisition_models/delivery_models为五张关系表，testcycle_schemas为请求约束，mount_service/acquisition_service/delivery_service为领域流转与计算，testcycle_routes为权限及事务。前端 pages/mounts、acquisitions、deliveries由store/api接入；新增状态同时在前后端constants声明。原Probe/Sweep/Layout/TunnelRun不加列不回填，历史快照不补造装夹；旧completed可保留查看，缺原始装夹与完整采集的历史试验不能伪造新交付。

扩展演练：先按原剧本完成LY-QA审签并给P09换发有效证书；编制RUN计划→录5kg/.2m²/45N·m/2000N装夹→主管验收并关联→负责人开车→建立2Hz×3s批次→各点录6个压力实样→主管冻结→工程师完结→交付给气动设计组→主管核准→登记签收。试缺一个通道或每通道只录2个样本会拒绝冻结；补齐后才可继续。

seed只补基础测点/历史扫角/演示证书，不自动审签或制造合格采样、装夹、回执；按剧本真实操作产生追加数据。重复seed保留人工装夹修订、实际序列、冻结状态、回执和原快照。v1/v2历史证据保留，追加验证在 `../../test-artifacts/gb-1028/v3/`。没有硬件采集接口/实时流/升力反演、自动停机、撤销冻结或真实文档外发；不将人工输入示例解释为真实风洞测试数据。

数据库使用READ COMMITTED，领域状态与父试验行锁继续串行化写入。采集冻结先读取批次再等试验锁，因此冻结汇总必须看到前一持锁事务最新提交的实样；不能沿用MySQL默认REPEATABLE READ在等锁前建立的旧快照。强制持锁2秒的实际并发测试验证：10Pa被重写为99Pa后冻结读到99Pa；完整采集被改成单通道后冻结拒绝，见v3/current-read-race-results.json。
