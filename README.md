# ORCA_Hopt-skills

用于个人 SMM 工作流的 Codex skill：将 XYZ 中的 **Dy 替换为 Y**，准备仅优化 H 的 ORCA 输入，默认按配位层重排原子，并逐条保留坐标数值原文。

默认参数格式以 [模板](references/orca-template.inp) 为准；完整工作规则见 [SKILL.md](SKILL.md)。**电荷与多重度按每个转换后的体系确定，`1 6` 不是默认值。**

## 安装与调用

仓库和显示名称为 `ORCA_Hopt-skills`，技能调用名及安装文件夹为 `orca-hopt-skills`。安装到 Codex 的 skills 目录（Windows 默认为 `%USERPROFILE%\.codex\skills`）：

```bash
git clone https://github.com/m7668/ORCA_Hopt-skills.git ~/.codex/skills/orca-hopt-skills
```

调用示例：

> 使用 $orca-hopt-skills 生成 Hopt 输入，把 Dy 换成 Y，按配位层重排。这个 Y 模型的电荷为 +1，多重度为 1。

代理从结构中确定金属和配位原子，处理有歧义的分配；脚本执行替换、重排和校验。替换会同时落实到坐标元素和金属基组设置，其他元素及全部坐标字符串保持不变。用户提供的参考输入优先，保留原子顺序或保留 Dy 等明确要求也优先。

## 独立使用脚本

Python 3.9+，仅使用标准库。以下电荷、多重度和配位编号均为示例，须替换为当前体系的值：

```bash
python scripts/prepare_input.py structure.xyz --charge 1 --multiplicity 1 --metal-atoms 1 --sphere-atoms 2,3,4,5,6,7,8 --output complex_Y_Hopt.inp --map atom-map.csv
```

默认使用保存的 Y 模板、自动执行 Dy → Y，并按“中心金属 → 第一配位层 → 其余重元素分组 → C → H”重排。金属和配位层内部按源文件顺序排列。源编号从第一个原子记为 1，不含 XYZ 计数行与注释行。

- `--keep-order`：明确保留源原子顺序，无需提供配位编号。
- `--sphere-atoms none`：配位层确实为空时使用。
- `--element-order Si,O,N`：其余重元素分组顺序，未列出的元素随后按首次出现顺序排列。
- `--template reference.inp`：使用参考输入，默认保留其元素；另加 `--dy-to-y` 才执行 Dy → Y，并更新受支持的按元素指定的基组/ECP 设置。仍需核实参考是否适合替换后的体系。
- `--map atom-map.csv`：输出从 0 和从 1 开始的编号对照，以及源元素、输出元素。

## 支持范围与校验

支持单帧标准 XYZ 或单个普通 `* xyz charge multiplicity` 坐标块。坐标记录必须为元素符号及三个有限数值，支持科学计数法和中文路径。多作业、轨迹、xyzfile、虚原子及附加字段等需另行处理。

验证原子总数、排列完整性、坐标字符串守恒及 Dy → Y 的元素计数变化；相同的重复记录也按次数保留。含编号敏感设置的参考输入需要核实对应关系；脚本检测到部分此类设置时会停止直接重排，且不会自动重写它们。

输出目录须存在，目标文件须尚不存在。脚本不运行 ORCA，也不验证电子态选择。运行环境和基组/ECP 核对见 [ORCA checks](references/orca-checks.md)；[2-Dy 记录](references/2-dy-example.md) 仅为历史案例。

## 开发验证

```bash
python -m unittest discover -s tests -v
```

测试覆盖元素替换、坐标及重复记录守恒、原子排序和映射、参考内容保留、异常输入和中文路径。
