// Mock Data for RetroCause Console
// 高保真数据模型 - 为组件树提供真实数据结构

export interface Hypothesis {
  id: string;
  title: string;
  probability: number;
  description: string;
  causalStrength: number;
  evidenceCount: number;
}

export interface Evidence {
  id: string;
  content: string;
  source: string;
  reliability: 'strong' | 'medium' | 'weak';
  causalWeight: number;
  timestamp: string;
}

export interface CausalNode {
  id: string;
  label: string;
  type: 'outcome' | 'factor' | 'intermediate';
  probability?: number;
  x?: number;
  y?: number;
}

export interface CausalEdge {
  id: string;
  source: string;
  target: string;
  strength: number;
  type: 'strong' | 'weak' | 'negative' | 'uncertain';
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  stance: 'support' | 'oppose' | 'neutral';
  contribution: string;
}

export interface ProbabilityBar {
  label: string;
  value: number;
  color?: string;
}

export interface GraphStats {
  nodeCount: number;
  edgeCount: number;
  confidence: number;
}

export interface EngineStatus {
  state: 'ready' | 'processing' | 'error';
  progress: number;
  causalChainCount: number;
  hypothesisCount: number;
  timestamp: string;
}

// Mock Data: 竞争假设列表
export const mockHypotheses: Hypothesis[] = [
  {
    id: 'H1',
    title: 'H1: 业绩下滑',
    probability: 78,
    description: 'Q3财报显示营收同比下降23%，净利润亏损扩大',
    causalStrength: 0.82,
    evidenceCount: 4,
  },
  {
    id: 'H2',
    title: 'H2: 竞争压力',
    probability: 65,
    description: '主要竞争对手发布革命性新品，市场份额被蚕食',
    causalStrength: 0.71,
    evidenceCount: 3,
  },
  {
    id: 'H3',
    title: 'H3: 宏观因素',
    probability: 42,
    description: '行业整体受宏观政策收紧影响，流动性紧缩',
    causalStrength: 0.45,
    evidenceCount: 2,
  },
  {
    id: 'H4',
    title: 'H4: 内部治理',
    probability: 31,
    description: 'CTO和CFO在暴跌前相继离职，内部信心不足',
    causalStrength: 0.38,
    evidenceCount: 2,
  },
  {
    id: 'H5',
    title: 'H5: 做空机构',
    probability: 28,
    description: '浑水研究发布做空报告，引发机构恐慌抛售',
    causalStrength: 0.52,
    evidenceCount: 3,
  },
];

// Mock Data: 证据列表
export const mockEvidences: Evidence[] = [
  {
    id: 'E1',
    content: '财报显示Q3营收同比下降23%，净利润亏损扩大至2.3亿元',
    source: '公司公告 (2024-01-10)',
    reliability: 'strong',
    causalWeight: 0.85,
    timestamp: '2024-01-10',
  },
  {
    id: 'E2',
    content: '竞品发布会后用户搜索量下降40%，应用商店排名跌出前100',
    source: '行业数据平台',
    reliability: 'medium',
    causalWeight: 0.62,
    timestamp: '2024-01-08',
  },
  {
    id: 'E3',
    content: '社交媒体负面舆情集中爆发，微博相关话题阅读量超5000万',
    source: '舆情监控系统',
    reliability: 'weak',
    causalWeight: 0.35,
    timestamp: '2024-01-12',
  },
  {
    id: 'E4',
    content: '机构持仓数据显示主要基金在暴跌前一周大幅减仓合计12%',
    source: '交易数据分析',
    reliability: 'strong',
    causalWeight: 0.78,
    timestamp: '2024-01-15',
  },
];

export type CausalNodeType = 'outcome' | 'factor' | 'intermediate';
export type EvidenceReliability = 'strong' | 'medium' | 'weak';
export type EdgeStrength = 'strong' | 'weak' | 'negative' | 'uncertain';

export interface ChainNodeDescription {
  brief: string;
  detail: string;
}

export interface ChainEdgeEvidence {
  evidenceId: string;
  content: string;
  reliability: EvidenceReliability;
  causalWeight: number;
}

export interface ChainNode {
  id: string;
  label: string;
  type: CausalNodeType;
  probability: number;
  depth: number;
  description: ChainNodeDescription;
  upstreamIds: string[];
  evidenceIds: string[];
}

export interface ChainEdge {
  id: string;
  source: string;
  target: string;
  strength: number;
  type: EdgeStrength;
  evidence: ChainEdgeEvidence[];
}

export interface CounterfactualSummary {
  intervention: string;
  outcomeChange: string;
  probabilityShift: number;
  description: string;
}

export interface UpstreamNode {
  id: string;
  label: string;
  probability: number;
  depth: number;
  type: CausalNodeType;
}

export interface UpstreamMap {
  [nodeId: string]: UpstreamNode[];
}

export interface ChainMetadata {
  id: string;
  title: string;
  outcomeLabel: string;
  totalNodes: number;
  totalEdges: number;
  maxDepth: number;
  confidence: number;
  primaryEvidenceCount: number;
  counterfactualSummary: CounterfactualSummary;
}

export interface CausalChain {
  metadata: ChainMetadata;
  nodes: ChainNode[];
  edges: ChainEdge[];
  upstreamMap: UpstreamMap;
}

export const mockPrimaryChain: CausalChain = {
  metadata: {
    id: 'CHAIN-001',
    title: '宏观政策收紧 → 竞争加剧 → 业绩下滑 → 信心危机 → 股票暴跌',
    outcomeLabel: '股票暴跌',
    totalNodes: 5,
    totalEdges: 4,
    maxDepth: 4,
    confidence: 0.87,
    primaryEvidenceCount: 6,
    counterfactualSummary: {
      intervention: '削弱「竞争加剧」环节',
      outcomeChange: '若竞争压力缓解，业绩下滑概率从78%降至约45%',
      probabilityShift: -33,
      description: '通过反事实干预模拟，竞争加剧环节是整个因果链的关键放大器。一旦该节点被削弱，传递到业绩下滑的条件概率显著下降。',
    },
  },
  nodes: [
    {
      id: 'CN1',
      label: '宏观政策收紧',
      type: 'factor',
      probability: 42,
      depth: 0,
      description: {
        brief: '监管层收紧流动性，行业融资成本上升',
        detail: '央行实施稳健货币政策，地方债务风险排查加速，银行对房地产及高负债行业惜贷情绪蔓延。融资环境收紧直接压缩企业扩张空间，导致行业内卷加剧。',
      },
      upstreamIds: [],
      evidenceIds: ['CE1', 'CE2'],
    },
    {
      id: 'CN2',
      label: '竞争加剧',
      type: 'intermediate',
      probability: 65,
      depth: 1,
      description: {
        brief: '行业内竞争白热化，利润空间被严重挤压',
        detail: '宏观流动性收紧背景下，行业头部玩家被迫争夺存量市场，促销战与价格战此起彼伏。中小玩家生存空间被进一步压缩，行业集中度短期反而上升，但整体利润池大幅缩水。',
      },
      upstreamIds: ['CN1'],
      evidenceIds: ['CE3', 'CE4'],
    },
    {
      id: 'CN3',
      label: '业绩下滑',
      type: 'factor',
      probability: 78,
      depth: 2,
      description: {
        brief: 'Q3财报营收同比下降23%，亏损幅度超出预期',
        detail: '在竞争加剧与成本上升的双重挤压下，公司核心业务盈利能力大幅下滑。营收同比减少23%，净亏损扩大至2.3亿元，机构投资者持仓信心开始松动。',
      },
      upstreamIds: ['CN1', 'CN2'],
      evidenceIds: ['CE5', 'CE6'],
    },
    {
      id: 'CN4',
      label: '信心危机',
      type: 'intermediate',
      probability: 55,
      depth: 3,
      description: {
        brief: '市场情绪恶化，机构与散户信心同步崩溃',
        detail: '业绩暴雷引发连锁反应：机构持仓大幅减持，社交媒体负面舆情集中爆发，高管离职进一步加剧市场对公司治理的担忧。恐慌情绪从机构传导至散户，形成负向正反馈。',
      },
      upstreamIds: ['CN3'],
      evidenceIds: ['CE7', 'CE8'],
    },
    {
      id: 'CN5',
      label: '股票暴跌',
      type: 'outcome',
      probability: 100,
      depth: 4,
      description: {
        brief: '股价在短期内大幅下跌，创历史最大单周跌幅',
        detail: '多重利空叠加下，股价在5个交易日内下跌47%，市值蒸发超过200亿元。融资盘爆仓与强制平仓形成踩踏，股价在技术性超卖区间仍未见明显支撑。',
      },
      upstreamIds: ['CN3', 'CN4'],
      evidenceIds: ['CE9', 'CE10'],
    },
  ],
  edges: [
    {
      id: 'CE1',
      source: 'CN1',
      target: 'CN2',
      strength: 0.72,
      type: 'strong',
      evidence: [
        { evidenceId: 'CE1', content: '央行Q3流动性报告显示M2增速降至8.1%，创历史新低', reliability: 'strong', causalWeight: 0.78 },
        { evidenceId: 'CE2', content: '商业银行对房地产相关行业贷款审批周期延长至45天以上', reliability: 'strong', causalWeight: 0.65 },
      ],
    },
    {
      id: 'CE2',
      source: 'CN2',
      target: 'CN3',
      strength: 0.81,
      type: 'strong',
      evidence: [
        { evidenceId: 'CE3', content: '行业价格战导致公司毛利率从34%压缩至21%', reliability: 'strong', causalWeight: 0.85 },
        { evidenceId: 'CE4', content: '竞品发布会后公司产品搜索指数下降40%', reliability: 'medium', causalWeight: 0.62 },
      ],
    },
    {
      id: 'CE3',
      source: 'CN3',
      target: 'CN4',
      strength: 0.76,
      type: 'strong',
      evidence: [
        { evidenceId: 'CE5', content: 'Q3财报发布后3个交易日内机构净卖出12%持仓', reliability: 'strong', causalWeight: 0.82 },
        { evidenceId: 'CE6', content: 'CTO与CFO在财报发布前相继提交辞呈', reliability: 'medium', causalWeight: 0.58 },
      ],
    },
    {
      id: 'CE4',
      source: 'CN4',
      target: 'CN5',
      strength: 0.89,
      type: 'strong',
      evidence: [
        { evidenceId: 'CE7', content: '股价在5个交易日内从¥42跌至¥22，跌幅47%', reliability: 'strong', causalWeight: 0.92 },
        { evidenceId: 'CE8', content: '融资融券余额在暴跌期间下降63%，强制平仓规模超5亿元', reliability: 'strong', causalWeight: 0.74 },
        { evidenceId: 'CE9', content: '社交媒体相关话题阅读量突破8000万，负面情绪占比超78%', reliability: 'medium', causalWeight: 0.55 },
      ],
    },
  ],
  upstreamMap: {
    'CN1': [],
    'CN2': [{ id: 'CN1', label: '宏观政策收紧', probability: 42, depth: 0, type: 'factor' }],
    'CN3': [
      { id: 'CN1', label: '宏观政策收紧', probability: 42, depth: 0, type: 'factor' },
      { id: 'CN2', label: '竞争加剧', probability: 65, depth: 1, type: 'intermediate' },
    ],
    'CN4': [{ id: 'CN3', label: '业绩下滑', probability: 78, depth: 2, type: 'factor' }],
    'CN5': [
      { id: 'CN3', label: '业绩下滑', probability: 78, depth: 2, type: 'factor' },
      { id: 'CN4', label: '信心危机', probability: 55, depth: 3, type: 'intermediate' },
    ],
  },
};

// Mock Data: 因果图节点
export const mockCausalNodes: CausalNode[] = [
  { id: 'N1', label: '股票暴跌', type: 'outcome', probability: 100, x: 50, y: 15 },
  { id: 'N2', label: '业绩下滑', type: 'factor', probability: 78, x: 20, y: 40 },
  { id: 'N3', label: '竞争压力', type: 'factor', probability: 65, x: 80, y: 40 },
  { id: 'N4', label: '宏观政策', type: 'intermediate', probability: 42, x: 15, y: 70 },
  { id: 'N5', label: '高管离职', type: 'intermediate', probability: 31, x: 40, y: 70 },
  { id: 'N6', label: '做空报告', type: 'intermediate', probability: 28, x: 60, y: 70 },
  { id: 'N7', label: '信心危机', type: 'intermediate', probability: 55, x: 35, y: 55 },
  { id: 'N8', label: '流动性收紧', type: 'factor', probability: 38, x: 85, y: 70 },
];

// Mock Data: 因果边
export const mockCausalEdges: CausalEdge[] = [
  { id: 'E1', source: 'N2', target: 'N1', strength: 0.82, type: 'strong' },
  { id: 'E2', source: 'N3', target: 'N1', strength: 0.71, type: 'strong' },
  { id: 'E3', source: 'N4', target: 'N2', strength: 0.65, type: 'strong' },
  { id: 'E4', source: 'N5', target: 'N2', strength: 0.45, type: 'weak' },
  { id: 'E5', source: 'N6', target: 'N1', strength: 0.52, type: 'strong' },
  { id: 'E6', source: 'N7', target: 'N1', strength: 0.58, type: 'strong' },
  { id: 'E7', source: 'N7', target: 'N5', strength: 0.62, type: 'strong' },
  { id: 'E8', source: 'N8', target: 'N3', strength: 0.38, type: 'weak' },
];

// Mock Data: Agent列表
export const mockAgents: Agent[] = [
  {
    id: 'A1',
    name: '侦探 Agent',
    role: '溯因推理',
    stance: 'support',
    contribution: '识别出业绩下滑作为主要驱动因素',
  },
  {
    id: 'A2',
    name: '逻辑 Agent',
    role: '演绎推理',
    stance: 'neutral',
    contribution: '验证因果链的逻辑完备性',
  },
  {
    id: 'A3',
    name: '统计 Agent',
    role: '归纳推理',
    stance: 'support',
    contribution: '基于历史数据计算条件概率',
  },
  {
    id: 'A4',
    name: '批判 Agent',
    role: '魔鬼代言',
    stance: 'oppose',
    contribution: '质疑宏观因素的因果强度',
  },
  {
    id: 'A5',
    name: '仲裁 Agent',
    role: '综合评估',
    stance: 'neutral',
    contribution: '平衡各方观点给出最终判断',
  },
];

// Mock Data: 概率分布
export const mockProbabilityBars: ProbabilityBar[] = [
  { label: 'H1-业绩', value: 78, color: 'var(--causal-strong)' },
  { label: 'H2-竞争', value: 65, color: 'var(--causal-strong)' },
  { label: 'H3-宏观', value: 42, color: 'var(--causal-uncertain)' },
  { label: 'H4-治理', value: 31, color: 'var(--causal-uncertain)' },
  { label: 'H5-做空', value: 28, color: 'var(--causal-weak)' },
];

// Mock Data: 图统计
export const mockGraphStats: GraphStats = {
  nodeCount: 8,
  edgeCount: 8,
  confidence: 87,
};

// Mock Data: 引擎状态
export const mockEngineStatus: EngineStatus = {
  state: 'ready',
  progress: 100,
  causalChainCount: 5,
  hypothesisCount: 12,
  timestamp: '2024-01-15 14:32:01',
};

// Mock Data: 筛选选项
export const timeRangeOptions = [
  { value: 'all', label: '全部时间' },
  { value: '24h', label: '近 24 小时' },
  { value: '7d', label: '近 7 天' },
  { value: '30d', label: '近 30 天' },
  { value: '1y', label: '近 1 年' },
];

export const causalStrengthOptions = [
  { value: 'all', label: '全部' },
  { value: 'strong', label: '强因果 (>0.8)' },
  { value: 'medium', label: '中因果 (0.5-0.8)' },
  { value: 'weak', label: '弱因果 (<0.5)' },
];

export const evidenceQualityOptions = [
  { value: 'all', label: '全部' },
  { value: 'high', label: '高可信度' },
  { value: 'medium', label: '中可信度' },
  { value: 'low', label: '低可信度' },
];

// Mock Data: Agent辩论报告 (Stage 5)
export interface DebateMetric {
  probability: number;
  confidence: number;
  evidenceIds: string[];
}

export interface DebateEvidence {
  id: string;
  content: string;
  type: 'support' | 'challenge';
  weight: number;
}

export interface AgentReport {
  id: string;
  agentName: string;
  agentRole: string;
  stance: 'support' | 'oppose' | 'neutral';
  phase: number;
  timestamp: string;
  conclusion: string;
  reasoning: string;
  metrics: DebateMetric;
  evidenceChain: DebateEvidence[];
  children?: AgentReport[];
}

export const mockAgentReports: AgentReport[] = [
  {
    id: 'R1',
    agentName: '侦探 Agent',
    agentRole: '溯因推理',
    stance: 'support',
    phase: 1,
    timestamp: '00:00.000',
    conclusion: 'H1(业绩下滑) 是本次股票暴跌的主要驱动因素，置信度 0.82',
    reasoning: 'IF Q3营收下降23% AND 机构持仓下降12% THEN 股价下跌。逆向溯因得：股价暴跌 ← 业绩下滑 ← 竞争失利',
    metrics: {
      probability: 78,
      confidence: 0.82,
      evidenceIds: ['E1', 'E2', 'E4'],
    },
    evidenceChain: [
      { id: 'E1', content: 'Q3营收同比下降23%，净利润亏损扩大至2.3亿元', type: 'support', weight: 0.85 },
      { id: 'E4', content: '机构持仓数据显示主要基金在暴跌前一周大幅减仓合计12%', type: 'support', weight: 0.78 },
      { id: 'E2', content: '竞品发布会后用户搜索量下降40%', type: 'support', weight: 0.62 },
    ],
  },
  {
    id: 'R2',
    agentName: '逻辑 Agent',
    agentRole: '演绎推理',
    stance: 'support',
    phase: 2,
    timestamp: '00:01.245',
    conclusion: '因果链 H1→N1 逻辑完备性验证通过，无矛盾路径',
    reasoning: '验证演绎链：(H1:业绩下滑) → (N7:信心危机) → (N1:股票暴跌)。各节点因果传递验证一致。',
    metrics: {
      probability: 81,
      confidence: 0.88,
      evidenceIds: ['E1', 'E4'],
    },
    evidenceChain: [
      { id: 'E1', content: '财报显示Q3营收同比下降23%', type: 'support', weight: 0.85 },
      { id: 'E4', content: '机构持仓数据显示主要基金在暴跌前一周大幅减仓', type: 'support', weight: 0.78 },
    ],
  },
  {
    id: 'R3',
    agentName: '统计 Agent',
    agentRole: '归纳推理',
    stance: 'support',
    phase: 3,
    timestamp: '00:02.189',
    conclusion: '基于历史数据的条件概率 P(暴跌|业绩下滑) = 0.76 ± 0.08',
    reasoning: '归纳计算：历史数据显示业绩下滑后30个交易日内暴跌概率为76%。贝叶斯更新后：P(H1|N1) = 0.78',
    metrics: {
      probability: 76,
      confidence: 0.75,
      evidenceIds: ['E1', 'E4'],
    },
    evidenceChain: [
      { id: 'E1', content: 'Q3财报营收下降23%', type: 'support', weight: 0.85 },
      { id: 'E4', content: '机构持仓下降12%', type: 'support', weight: 0.78 },
    ],
  },
  {
    id: 'R4',
    agentName: '批判 Agent',
    agentRole: '魔鬼代言',
    stance: 'oppose',
    phase: 4,
    timestamp: '00:03.456',
    conclusion: 'H1 存在反向因果风险：暴跌可能导致信心危机而非业绩下滑',
    reasoning: '反驳：机构减仓(E4)可能既是暴跌的果，也是因。时序分析显示E4与暴跌时间窗口重叠，无法确定因果方向。',
    metrics: {
      probability: 42,
      confidence: 0.65,
      evidenceIds: ['E3', 'E4'],
    },
    evidenceChain: [
      { id: 'E3', content: '社交媒体负面舆情集中爆发', type: 'challenge', weight: 0.35 },
      { id: 'E4', content: '机构持仓在暴跌前一周减仓12%', type: 'challenge', weight: 0.78 },
    ],
  },
  {
    id: 'R5',
    agentName: '溯因 Agent',
    agentRole: '溯因推理',
    stance: 'neutral',
    phase: 1,
    timestamp: '00:00.320',
    conclusion: 'H3(宏观因素) 可作为竞争假设：政策收紧 → 行业下行 → 业绩下滑',
    reasoning: '溯因备选路径：宏观政策收紧 → 行业流动性紧缩 → 竞争加剧 → 业绩下滑。需与H1比较先验概率。',
    metrics: {
      probability: 42,
      confidence: 0.55,
      evidenceIds: ['E2'],
    },
    evidenceChain: [
      { id: 'E2', content: '竞品发布会后用户搜索量下降40%', type: 'support', weight: 0.62 },
    ],
  },
  {
    id: 'R6',
    agentName: '批判 Agent',
    agentRole: '魔鬼代言',
    stance: 'oppose',
    phase: 4,
    timestamp: '00:04.102',
    conclusion: 'H3 支撑证据不足：E2 为弱证据(0.62)，无法建立强因果链',
    reasoning: 'E2显示搜索量下降，但未直接关联宏观政策。行业整体数据缺失，H3的因果强度不足。',
    metrics: {
      probability: 38,
      confidence: 0.58,
      evidenceIds: ['E2'],
    },
    evidenceChain: [
      { id: 'E2', content: '用户搜索量下降40%，应用商店排名跌出前100', type: 'challenge', weight: 0.62 },
    ],
  },
  {
    id: 'R7',
    agentName: '仲裁 Agent',
    agentRole: '仲裁',
    stance: 'neutral',
    phase: 5,
    timestamp: '00:05.000',
    conclusion: '最终裁定：H1(业绩下滑) 为主要因素，P=0.78；H3(宏观) 为次要因素，P=0.38',
    reasoning: '综合评分：H1得 分(0.82×0.88×0.76)=0.548；H3得分(0.55×0.58)=0.319。H1压倒性胜出，建议聚焦H1进行因果分析。',
    metrics: {
      probability: 78,
      confidence: 0.91,
      evidenceIds: ['E1', 'E2', 'E4'],
    },
    evidenceChain: [
      { id: 'E1', content: 'Q3营收下降23%，强因果', type: 'support', weight: 0.85 },
      { id: 'E4', content: '机构减仓12%，强因果', type: 'support', weight: 0.78 },
      { id: 'E2', content: '搜索量下降40%，弱因果', type: 'support', weight: 0.62 },
    ],
  },
];
