# 协作工作流

## 角色

| 角色 | Agent | 职责 |
|------|-------|------|
| 助理 | Echo (main) | 接收需求，创建任务 |
| 产品经理 | pm | 设计方案，输出文档 |
| 开发者 | genius-coder | 编写代码，提交PR |

## 工作流程

```
1. 你向 Echo 提需求
      ↓
2. Echo 创建 GitHub Issue（标签: todo）
      ↓
3. PM 定时检查 → 开始设计
      ↓
4. 设计完成 → 更新 Issue（标签: ready-dev） + 文档存入 docs/design/
      ↓
5. Developer 定时检查 → 开始开发
      ↓
6. 开发完成 → 提交 PR → 更新 Issue（标签: done）
      ↓
7. 你确认后合并 PR
```

## 任务示例

**需求**: 添加一个 RSI 择时策略

**Issue 标题**: `[策略] RSI 择时策略`

**流程**:
1. PM 设计文档: `docs/design/rsi-strategy.md`
2. Developer 实现: `strategies/rsi_strategy.py`
3. 提交 PR: "feat: 添加 RSI 择时策略"

## 协作工具

- **任务管理**: GitHub Issues
- **设计文档**: `quant-trading/docs/design/`
- **代码仓库**: https://github.com/kapokheaven19-cpu/quant-trading
