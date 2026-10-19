# ORCA_Hopt-skills

用于个人 SMM 工作流的 Codex skill：从 XYZ 或普通 ORCA 笛卡尔坐标块准备 `.inp`，保留坐标原文，按需整理配位层顺序。

默认沿用长期保存的“仅优化 H”方案。**默认协议、参数来源和操作规则以 [SKILL.md](SKILL.md) 及其链接的模板为准**；用户提供的参考输入优先。

## 安装与调用

仓库和显示名称为 `ORCA_Hopt-skills`；技能标识和调用名为 `orca-hopt-skills`，采用小写字母和连字符。

将仓库克隆或解压到 Codex 的 skills 目录，安装文件夹命名为 `orca-hopt-skills`，确保路径为 `~/.codex/skills/orca-hopt-skills/SKILL.md`。Windows 的默认目录为 `%USERPROFILE%\.codex\skills`。例如：

```bash
git clone https://github.com/m7668/ORCA_Hopt-skills.git ~/.codex/skills/orca-hopt-skills
```

重新加载技能后可直接调用：

> 使用 $orca-hopt-skills，按默认仅优化 H 方案处理这份 XYZ。电荷 +1、多重度 6，保留原子顺序。

需要重排时明确提出“中心金属 → 第一配位层 → 其余重原子 → C → H”，并提供已知配位原子编号。没有编号时由代理结合结构判断，存在影响结果的歧义再讨论。

## 独立使用脚本

Python 3.9+，仅使用标准库，不需要安装第三方依赖。下面的电荷和多重度只是调用示例，须替换为当前体系的已确认值：

```bash
python scripts/prepare_input.py structure.xyz --charge 1 --multiplicity 6 --output complex.inp
```

请求重排并输出编号映射：

```bash
python scripts/prepare_input.py structure.xyz --charge 1 --multiplicity 6 --reorder --metal-atoms 1 --sphere-atoms 2,3,4,5,6,7 --output complex.inp --map atom-map.csv
```

编号从源文件第一个原子记为 1，不包含 XYZ 的计数行和注释行。金属和第一配位层内部保持源文件顺序，参数中的先后顺序不改变这一规则。`--element-order Si,O,N` 可指定其余重元素分组顺序；未列出的元素随后按源文件首次出现顺序排列。

使用其他参考输入时加 `--template reference.inp`。参考可以是含一个普通 `* xyz` 块的输入，或与内置模板相同的占位块。脚本只更换坐标块和明确给定的电荷/多重度，不自行选方法、分配 ECP 或重写原子编号设置。

## 支持范围与校验

- 单帧标准 XYZ；或单个普通 `* xyz charge multiplicity` 块。普通记录为元素符号和三个有限数值，支持科学计数法和中文路径。
- 输出前验证原子数、坐标记录与排列完整性，保留每条原子行及坐标字符串；重复的相同坐标记录也按次数保留。
- 发现受支持检查覆盖的编号敏感设置时，拒绝直接重排。代理须先核实对应关系；编号映射文件同时包含从 0 和从 1 开始的两组列。
- 多作业、轨迹、多坐标块、xyzfile、虚原子、原子附加字段等格式不由此脚本处理。它是有限的文件转换器，不是完整 ORCA 解析器。
- 输出目录须已存在，输出文件须尚不存在。脚本不运行 ORCA；文件校验通过不等于电子态、基组/ECP 或运行兼容性已经验证。

`2-Dy` 的历史设定见 [案例记录](references/2-dy-example.md)，不作为新体系默认值。基组、编号和运行时资源的核对说明见 [ORCA checks](references/orca-checks.md)。

## 开发验证

```bash
python -m unittest discover -s tests -v
```

测试使用合成小结构检查记录守恒、重复记录、排列与编号、参考内容保留、异常输入和中文路径，不替代真实体系的 ORCA 运行验证。
