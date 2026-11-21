"""Chinese L1 discovery queries for the MindForge skill catalog.

Use with::

    uv run smelt discover ../skills/zh-cn \
        --distractors discovery/distractors/zh-cn \
        --queries discovery/zh_cn_queries.py --repeat 2

The 15 train rows are for iteration; the 11 test rows are the CI gate.
"""

from smelt import discovery_query

queries = [
    discovery_query(
        "结账时重复扣款。先画出订单和支付的表结构以及主键关系。",
        gold=["database-design"], kind="positive", split="train", name="db-orders",
    ),
    discovery_query(
        "挑选一种可复用的结构，替代结算流程中不断增加的 if-else 分支。",
        gold=["design-pattern"], kind="paraphrase", split="test", name="pattern-checkout",
    ),
    discovery_query(
        "Java 服务在虚拟线程进入 synchronized 代码块后卡住。",
        gold=["enterprise-java"], kind="positive", split="test", name="java-pinning",
    ),
    discovery_query(
        "在 Next.js 应用的服务端渲染路由里增加一个带数据获取的表单。",
        gold=["frontend-react"], kind="positive", split="train", name="react-route",
    ),
    discovery_query(
        "为 SvelteKit 路由写一个单文件表单组件。",
        gold=["frontend-svelte"], kind="positive", split="test", name="svelte-form",
    ),
    discovery_query(
        "Nuxt 应用的两个页面要读取同一个共享状态，请接好它。",
        gold=["frontend-vue"], kind="positive", split="train", name="vue-store",
    ),
    discovery_query(
        "找出让构建失败的提交，然后整理最近的提交历史。",
        gold=["git-guru"], kind="paraphrase", split="test", name="git-regression",
    ),
    discovery_query(
        "后台任务在请求结束后还活着，因为取消信号被忽略了。",
        gold=["go-development"], kind="positive", split="train", name="go-cancel",
    ),
    discovery_query(
        "收紧这个模块，让编译器拒绝混用不同类型的值。",
        gold=["javascript-typescript"], kind="paraphrase", split="train", name="ts-strict",
    ),
    discovery_query(
        "设计带版本控制和幂等重试的公开评论接口。",
        gold=["api-design"], kind="positive", split="test", name="api-comments",
    ),
    discovery_query(
        "写一份密码重置功能的一页式产品说明和最小首版范围。",
        gold=["product-management"], kind="positive", split="train", name="pm-reset",
    ),
    discovery_query(
        "我的迭代器在第二次遍历循环时没有产出任何值。",
        gold=["python-development"], kind="positive", split="test", name="py-generator",
    ),
    discovery_query(
        "准备一份交接说明，让明天的会话拥有同样的上下文。",
        gold=["session-summary"], kind="positive", split="train", name="handover",
    ),
    discovery_query(
        "两个任务修改同一个模型，编译器报告数据竞争。",
        gold=["swift-development"], kind="positive", split="test", name="swift-race",
    ),
    discovery_query(
        "在 iOS 界面里展示可滚动列表和详情页面。",
        gold=["swiftui-development"], kind="paraphrase", split="train", name="swiftui-list",
    ),
    discovery_query(
        "把两种系统设计方案的选择写成架构决策记录。",
        gold=["system-architecture"], kind="positive", split="test", name="adr",
    ),
    discovery_query(
        "给运维团队一份上线步骤指南和告警处理手册。",
        gold=["tech-documentation"], kind="paraphrase", split="train", name="runbook",
    ),
    discovery_query(
        "在发布前为折扣计算器补充单元测试用例。",
        gold=["testing"], kind="positive", split="test", name="unit-cases",
    ),
    discovery_query(
        "新加的源文件没有出现在 Xcode 项目导航器里。",
        gold=["xcode-management"], kind="positive", split="train", name="xcode-file",
    ),
    discovery_query(
        "把这张发票 PDF 原样转发给客户，不要改动内容。",
        kind="near-miss", split="test", name="forward-pdf",
    ),
    discovery_query(
        "推荐火车站附近的一家咖啡馆。",
        kind="near-miss", split="train", name="coffee",
    ),
    discovery_query(
        "上海明天天气怎么样？",
        kind="none", split="test", name="weather",
    ),
    discovery_query(
        "计算半径为 7 的圆面积。",
        kind="none", split="train", name="math",
    ),
]
