// StoryOS 工作区历史证据快照（非实时生产状态）；按消费场景拆包。
export const REAL_AGENTS = [
  {
    "agent_code": "story-director",
    "agent_name": "剧本总编导智能体",
    "agent_type": "Creative Orchestrator",
    "status": "ACTIVE",
    "description": "负责故事种子初始化、大纲节拍表锁定、三层 Gate 门禁与 Story Lock 语义一致性裁决。"
  },
  {
    "agent_code": "codex-image-worker",
    "agent_name": "Codex 渲染推理智能体",
    "agent_type": "Execution Engine",
    "status": "ACTIVE",
    "description": "管理隔离的 GPU 推理 Worker 池，按 DAG 拓扑并发派发出图任务，自动执行指数退避与技术重试。"
  },
  {
    "agent_code": "semantic-critic",
    "agent_name": "逐帧语义审核智能体",
    "agent_type": "Quality Assurance",
    "status": "ACTIVE",
    "description": "针对生成成片执行全量逐帧语义审查，校准主角面容一致性、服装锚点、真实皮肤纹理与画幅合规性。"
  },
  {
    "agent_code": "gate-evaluator",
    "agent_name": "质量门禁判定智能体",
    "agent_type": "Governance Gate",
    "status": "ACTIVE",
    "description": "执行 Machine Gate 与 Evidence Gate 证据闭环判定，对发布前 Preflight、字幕安全区与防塑料感进行强校验。"
  },
  {
    "agent_code": "canvas-normalizer",
    "agent_name": "画幅标准化智能体",
    "agent_type": "Pixel Processor",
    "status": "ACTIVE",
    "description": "强制执行 4:5 1080×1350 叙事画幅，提供 Lanczos 算法重采样、无拉伸适配与像素主色彩审计。"
  },
  {
    "agent_code": "trace-observer",
    "agent_name": "链路追踪与日志智能体",
    "agent_type": "Observability",
    "status": "ACTIVE",
    "description": "监控并记录从 Request 到 Snapshot 的端到端分布式 Trace Span，提供毫秒级诊断日志与异常预警。"
  }
];
