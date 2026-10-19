# ORCA_Hopt-skills

个人 SMM 计算输入准备工具集，包含两个可分别安装和调用的 Codex skill。

| Skill | 用途 | 目录 |
|---|---|---|
| `$orca-hopt-skills` | 默认 Dy → Y、按配位层重排，生成 ORCA 仅优化 H 输入 | [skills/orca-hopt-skills](skills/orca-hopt-skills) |
| `$molcas-smm` | 准备原生 MOLCAS/OpenMolcas Dy(III) CASSCF → RASSI → SINGLE_ANISO 输入 | [skills/molcas-smm](skills/molcas-smm) |

## 安装

将所需的 skill 文件夹复制到 Codex skills 目录：

- `skills/orca-hopt-skills` → `~/.codex/skills/orca-hopt-skills`
- `skills/molcas-smm` → `~/.codex/skills/molcas-smm`

Windows 默认 skills 目录为 `%USERPROFILE%\.codex\skills`。也可以直接让 Codex 的 skill-installer 从此仓库安装对应子路径。**不要把整个仓库根目录作为单个 skill 安装。** 现有 Hopt 本地安装路径不受目录整理影响；以后更新时使用上述子路径。

## 工作流衔接

1. `$orca-hopt-skills` 从结构生成 Y 替代模型的 Hopt 输入；ORCA 优化需要另行执行。
2. 获取优化后的坐标，并完成所需的金属居中处理。
3. `$molcas-smm` 在明确要求时将指定中心 Y 恢复为 Dy，按实际体系核算电子数，生成磁性计算输入。

坐标不是初始轨道文件。MOLCAS 的 `lumorb` 需要与输出几何、中心顺序、Dy 基组及活性空间匹配的 INPORB；该 skill 不会凭空生成或认定轨道已就绪。各阶段的电荷和多重度按其实际模型确定，不固定沿用 ORCA 示例参数。

详细规则、模板和使用限制分别以各 skill 的 `SKILL.md` 为准。两个 skill 都区分静态文件检查与真实计算结果。

## 验证

Python 标准库测试：

```bash
python -m unittest discover -s skills/orca-hopt-skills/tests -v
python -m unittest discover -s tests -v
```

测试覆盖 Hopt 坐标操作，以及 MOLCAS 随附案例的原子记录、标签、电子数和状态清单；不代替 ORCA/MOLCAS 实际运行。
