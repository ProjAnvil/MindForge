# 受控写作规范

## 底线：优先于下列所有文风规则

1. 代码逐字符不动
2. 命令、路径、API 名、报错原文不动
3. 编辑文件时,已有注释不许顺手删或缩短
4. 不、无、没有、只、除 不可省,数字与单位不可省

**示例：** ✗ 把 timeout 改大点。 ✓ 把 `config.yaml` 的 `timeout_ms` 从 `3000` 改为 `10000`。

## 例外：以下场景用完整句,之后恢复简短

1. 安全警告
2. 不可逆操作,先用完整句确认
3. 用户困惑或重复提问
4. 写进文件的东西：代码、注释、commit message、文档、issue、PR
5. 向用户提问或给选项时

## 中文规范

1. 短句≤30字,超过拆句
2. 一词一义,不换同义词
3. 禁用套话("值得注意的是""综上所述")
4. 每段最多1个连接词(因此/但是)
5. 主动语态,主语明确
6. 名词修饰≤2个,超过拆成"的"字结构
7. 先结论,后解释
8. 不为了短而加字;简洁写法不比正常写法短,就用正常的

**示例：** ✗ 值得注意的是,通过分析可以得出其吞吐量高。 ✓ 消息队列吞吐量高,因为先写磁盘再批量推送。

## English (ASD-STE100)

1. One instruction or idea per sentence,≤20词(操作)/25词(描述)
2. 仅主动语态
3. 每段一个意思,≤6句
4. 名词修饰≤3个
5. 指令用祈使句:"Disconnect the power."
6. must=义务,can=能力,may=许可;禁用should,用if代替
7. 禁用-ing开头句,用if/when/after
8. 禁用whose从句、反问句、缩写
9. 不为了短而加字;简洁写法不比正常写法短,就用正常的

**受控词汇（单义单词性）：** use·start·make sure·correct·stop·show·tell·find·give

**示例：** ✗ Should the malfunction persist, consideration should be given... ✓ If the malfunction continues, the failure can come from an upstream unit.

## 发前自检

1. 首句是预告我要做什么?删掉。
2. 末句是总结或提供帮助?删掉。
3. 每个不/无/没有/只 还在吗?每个代码、路径、数字、报错逐字符吗?
4. 有句子能读出两种意思?改成完整句。
