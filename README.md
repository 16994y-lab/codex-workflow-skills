# Codex 工作流技能

三个可独立安装的技能，分别用于项目启动与交接、人工复核和算力规划。可以只安装需要的一项。

| 技能 | 什么时候用 | 交付 |
| --- | --- | --- |
| [项目启动与交接](project-kickoff/SKILL.md) | 新项目开工、接手已有项目或明确重定范围时 | 最小可验收结果、工作范围、验证方式和接手入口 |
| [人工复核协作](human-review-collaboration/SKILL.md) | 准备需要真人判断的材料、收集标注或处理审核反馈时 | 可直接判断的证据、具体问题和结果记录 |
| [算力与 Colab 执行](compute-colab-runner/SKILL.md) | 需要比较本机和云端资源，或准备可续跑的计算任务时 | 资源评估、运行计划、保存与恢复步骤 |

## 安装和使用

在 [Releases](https://github.com/16994y-lab/codex-workflow-skills/releases/latest) 下载对应的 ZIP，解压后将其中的同名目录放入 Codex 使用的技能目录。也可以从这个仓库单独复制相应目录。保留技能目录结构，使 `SKILL.md` 可以找到它引用的文件。

以下示例可直接用于新会话。

- 使用 `$project-kickoff` 规划一个社区图书借阅小工具，给出首版范围和验收标准。
- 使用 `$human-review-collaboration` 把这批模拟样本整理成可以逐项确认的审核清单，区分事实判断和执行批准。
- 使用 `$compute-colab-runner` 检查一个小型图像分类实验适合本机还是 Colab。预算为零，本次只评估。

算力技能提供可选的本机检查脚本，仅依赖 Python 标准库。NVIDIA 查询需要系统能找到 `nvidia-smi`。电池和供电检查目前适用于 Windows。脚本输出可能含本地路径和设备信息，分享报告前请移除这些字段。

## 许可

仓库及三个独立安装包采用 [MIT 许可](LICENSE)。
