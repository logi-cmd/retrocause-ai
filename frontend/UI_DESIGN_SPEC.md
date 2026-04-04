# RetroCause UI Design Specification
## 逆向因果探索引擎 - 前端设计规范

---

## 1. Design Philosophy / 设计哲学

**核心理念**: "客观、数据驱动、冰冷但清晰的逻辑推演"

RetroCause UI 的设计目标是传达专业数据分析工具的质感，类似于 Bloomberg Terminal、Reuters Eikon、或专业金融/数据科学分析软件。界面应该让用户感受到：
- 严肃性和可信度
- 信息密度与清晰度的平衡
- 冷峻、理性、不带情感色彩的技术美感
- 精确与克制的视觉语言

**禁止元素**:
- 紫色/粉色/彩虹色渐变
- 毛玻璃效果 (glassmorphism)
- 动态流体背景
- 圆角卡片堆砌
- 对话式 AI 聊天气泡 UI
- 任何 "AI 感" 视觉元素

---

## 2. Design Language / 设计语言

### 2.1 Aesthetic Direction
**参考**: Bloomberg Terminal + Linear App + 专业监控仪表盘

特征:
- 极高信息密度
- 等宽字体用于数据展示
- 锐利的边框和分割线
- 无装饰性元素
- 静态为主，交互通过微妙的亮度变化反馈

### 2.2 Color Palette / 色彩系统

#### 基础色 (Neutral Scale)
```
--neutral-950: #0A0A0A    /* 背景底色 */
--neutral-900: #111111    /* 主背景 */
--neutral-850: #171717    /* 卡片背景 */
--neutral-800: #1F1F1F    /* 次级卡片 */
--neutral-700: #2A2A2A    /* 边框加深 */
--neutral-600: #3A3A3A    /* 禁用状态 */
--neutral-500: #525252    /* 次要文字 */
--neutral-400: #737373    /* 占位符 */
--neutral-300: #A3A3A3    /* 辅助文字 */
--neutral-200: #D4D4D4    /* 主要文字 */
--neutral-100: #E5E5E5    /* 强调文字 */
--neutral-50:  #FAFAFA    /* 纯白文字 */
```

#### 品牌色 (Brand Colors)
```
--brand-primary:    #0066CC    /* 品牌蓝 - 主要操作 */
--brand-secondary:  #004999    /* 深蓝 - 悬停状态 */
--brand-muted:       #003366    /* 暗蓝 - 选中状态背景 */
```

#### 功能色 (Semantic Colors)
```
--success:          #10B981    /* 正向因果 / 确认 */
--warning:          #F59E0B    /* 中性 / 待定 */
--error:            #EF4444    /* 负向 / 否定 / 强对立 */
--info:             #3B82F6    /* 信息提示 */

--causal-strong:    #22C55E    /* 强因果关系 */
--causal-weak:      #84CC16    /* 弱因果关系 */
--causal-negative:  #EF4444    /* 负向因果 */
--causal-uncertain: #F59E0B    /* 不确定因果 */
```

#### 边框与分割线
```
--border-subtle:    #2A2A2A    /* 细微分割线 */
--border-default:   #3A3A3A    /* 默认边框 */
--border-strong:    #525252    /* 强调边框 */
```

### 2.3 Typography / 字体系统

**字体选择**:
- 界面字体: Inter (但使用极细 weight, 300-500)
- 数据/代码字体: JetBrains Mono / IBM Plex Mono
- 中文字体: Noto Sans SC (极细)

**Type Scale**:
```
--text-xs:    11px / 1.4    /* 最小数据标签 */
--text-sm:    12px / 1.5    /* 次要信息 */
--text-base:  14px / 1.5    /* 正文 */
--text-lg:    16px / 1.4    /* 标题辅助 */
--text-xl:    20px / 1.3    /* 区块标题 */
--text-2xl:   24px / 1.2    /* 页面标题 */
```

**字重控制**:
- Regular (400): 正文
- Medium (500): 标签、重要数据
- Semibold (600): 标题 (慎用)

### 2.4 Spacing & Grid / 间距系统

**Base Unit**: 4px

**Spacing Scale**:
```
--space-1:  4px
--space-2:  8px
--space-3:  12px
--space-4:  16px
--space-5:  20px
--space-6:  24px
--space-8:  32px
--space-10: 40px
--space-12: 48px
```

**Border Radius**:
```
--radius-none: 0        /* 默认无圆角 */
--radius-sm:  2px      /* 极小圆角 - 仅用于按钮 */
--radius-md:  4px      /* 中等 - 表格单元格 */
```

### 2.5 Motion Philosophy / 动效哲学

**核心原则**: 最小化动效，仅在必要时使用

- **过渡时间**: 100-150ms (极快)
- **缓动函数**: `ease-out` 或线性
- **允许的动效**:
  - 按钮/卡片的 hover 亮度变化 (opacity 或 brightness)
  - 下拉菜单展开
  - 模态框淡入
  - 数据加载的骨架屏
- **禁止的动效**:
  - 弹跳、弹性、夸张的进入动画
  - 背景渐变流动
  - 任何 "有机" 感运动

---

## 3. Layout System / 页面框架

### 3.1 Overall Layout Structure

**三栏布局 (Three-Column Console Layout)**:

```
┌─────────────────────────────────────────────────────────────────────┐
│ HEADER: 极简顶栏 (32px高) - Logo + 核心导航 + 状态指示器              │
├───────────┬─────────────────────────────────────────┬───────────────┤
│           │                                         │               │
│  LEFT     │  MAIN CANVAS                            │  RIGHT        │
│  PANEL    │  (因果图/辩论过程)                       │  PANEL        │
│           │                                         │               │
│  控制面板   │  核心可视化区域                          │  证据/详情     │
│  240px    │  flex-1                                 │  320px        │
│           │                                         │               │
│  - 输入    │  - 因果图                               │  - 节点详情    │
│  - 过滤器  │  - 辩论树                               │  - 证据列表    │
│  - 层级导航 │  - 数据表格                             │  - 概率分布    │
│           │                                         │               │
├───────────┴─────────────────────────────────────────┴───────────────┤
│ STATUS BAR: 16px - 系统状态 + 运算进度 + 时间戳                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Page Sections / 页面区块

#### 3.2.1 Header (32px)
```
[Logo] │ [探索新的因果链] [我的因果链] [假设库] [设置]    │ [●] 已连接
```
- 极简，纯文字导航
- 无 logo 动画
- 状态指示器仅用小圆点表示连接状态

#### 3.2.2 Left Panel - Control Panel (240px)
**核心功能**:
- **Query Input**: 文本输入框，用户输入"结果"
- **Filters**: 时间范围、因果强度、证据质量过滤
- **Hypothesis List**: 假设列表，支持折叠/展开
- **Layer Navigation**: 因果链层级导航

**视觉特征**:
- 深色背景 (#0A0A0A)
- 锐利的底边分割线
- 分组标题使用极小字号 (11px) + 大写字母间距

#### 3.2.3 Main Canvas - 可变区域
**三种视图模式**:

1. **因果图视图 (Causal Graph View)**
   - 节点: 方形/矩形，锐边
   - 边: 直线箭头，颜色编码因果强度
   - 交互: 点击节点显示详情，悬停显示概率

2. **辩论树视图 (Debate Tree View)**
   - 多角色 Agent 的论点树
   - 支持/反对用颜色区分
   - 折叠/展开节点

3. **数据表格视图 (Data Table View)**
   - 高密度数据网格
   - 固定表头，横向滚动
   - 极窄行高 (32px)

#### 3.2.4 Right Panel - Detail Panel (320px)
**信息展示**:
- 选中节点/假设的详细信息
- 证据列表 (带来源可靠性评分)
- 概率分布图 (静态柱状图)
- 推理链日志

#### 3.2.5 Status Bar (16px)
```
[⚡ 引擎就绪] │ [处理中: 23%] │ [因果链: 12] │ [假设: 5] │ [2024-01-15 14:32:01]
```

### 3.3 Responsive Strategy

**断点**:
- `>= 1440px`: 完整三栏布局
- `1024-1439px`: 可折叠左右面板
- `< 1024px`: 单栏堆叠，底部 Tab 导航

---

## 4. Component Library / 组件规范

### 4.1 Typography Components

| 组件 | 字号 | 字重 | 用途 |
|------|------|------|------|
| Display | 24px | 500 | 页面主标题 |
| Heading | 16px | 500 | 区块标题 |
| Label | 12px | 500 | 表单标签、列头 |
| Body | 14px | 400 | 正文内容 |
| Mono | 13px | 400 | 数据、代码 (等宽) |
| Caption | 11px | 400 | 辅助说明 |

### 4.2 Button Variants

```typescript
// Primary Button - 品牌蓝背景
bg-brand-primary, text-white, rounded-sm, h-8, px-3

// Secondary Button - 透明背景 + 边框
bg-transparent, border border-neutral-700, text-neutral-200, rounded-sm

// Ghost Button - 仅文字
bg-transparent, text-neutral-300, hover:text-white

// Danger Button
bg-error/10, text-error, border border-error/30, rounded-sm
```

### 4.3 Input Fields

```typescript
// Text Input
bg-neutral-900, border border-neutral-700, rounded-sm
focus: border-brand-primary, outline-none
h-8, px-3, text-sm

// Textarea
同 Input，min-h-24

// Select Dropdown
同 Input + Chevron icon
```

### 4.4 Data Display

#### Badge / Tag
```
bg-neutral-800, text-neutral-300, border border-neutral-700, px-2, py-0.5, text-xs
```

#### Probability Indicator
```
[████████░░] 80%  - 实心方块表示概率
```

#### Evidence Card
```
bg-neutral-850, border-l-2 border-[color-coded], p-3
```

### 4.5 Causal Graph Nodes

```typescript
// Factor Node (原因节点)
bg-neutral-800, border border-neutral-600, rounded-none, p-2

// Outcome Node (结果节点)
bg-neutral-850, border border-brand-primary, font-medium

// Intermediate Node
bg-neutral-800, border border-neutral-700

// Node States
hover: border-neutral-500
selected: border-brand-primary, bg-brand-muted/20
```

### 4.6 Table

```typescript
// Table Container
bg-neutral-900, border border-neutral-700

// Table Header
bg-neutral-950, text-neutral-400, text-xs, uppercase, letter-spacing: 0.05em

// Table Row
border-b border-neutral-800, hover:bg-neutral-850/50

// Table Cell
px-3, py-2, text-sm
```

### 4.7 Status Indicators

```typescript
// 在线/成功
w-2, h-2, rounded-full, bg-success

// 处理中
w-2, h-2, rounded-full, bg-warning, animate-pulse (仅用于真正处理中)

// 错误/离线
w-2, h-2, rounded-full, bg-error
```

---

## 5. Interaction Patterns / 交互模式

### 5.1 Hover States
- 所有可交互元素必须有 hover 状态
- 使用 `brightness` 或 `opacity` 变化
- 不使用 `scale` 变换 (避免布局抖动)

### 5.2 Focus States
- 使用 `ring-1 ring-brand-primary` 
- 不使用默认浏览器 outline

### 5.3 Loading States
- 使用骨架屏 (Skeleton)
- 骨架颜色: `bg-neutral-800`
- 不使用 Spinner (除非极小空间)

### 5.4 Empty States
- 简洁的文字说明
- 可选: 极简的示意线条图

### 5.5 Error States
- 红色边框 + 红色文字说明
- 不使用 Toast/Popup

---

## 6. Technical Specifications / 技术规范

### 6.1 Color Application Rules
- 所有颜色通过 CSS 变量使用
- 禁止硬编码颜色值
- 深色模式为默认 (唯一模式)

### 6.2 Tailwind CSS Configuration
```typescript
// 扩展 color palette
colors: {
  neutral: { 950, 900, 850, 800, 700, 600, 500, 400, 300, 200, 100, 50 },
  brand: { primary, secondary, muted },
  causal: { strong, weak, negative, uncertain },
  semantic: { success, warning, error, info }
}

// 禁用 border-radius 扩展 (使用默认值或 none)
borderRadius: { DEFAULT: '2px' }

// 字体配置
fontFamily: { mono: ['JetBrains Mono', 'IBM Plex Mono'] }
```

### 6.3 Icon Library
- 使用 Lucide Icons (线性风格)
- 图标尺寸: 16px (标准), 14px (紧凑)
- 图标颜色: `text-neutral-400` (标准), `text-neutral-500` (禁用)

---

## 7. Anti-Patterns / 禁止的模式

1. **禁止**: 任何紫色/粉色/渐变色
2. **禁止**: `backdrop-blur` 毛玻璃效果
3. **禁止**: `border-radius-xl` 或更大的圆角
4. **禁止**: `animate-bounce` 或 `animate-pulse` (除非真正的 loading)
5. **禁止**: 纯装饰性的背景图案
6. **禁止**: ChatGPT 式的消息气泡 UI
7. **禁止**: 彩虹色或多彩的 "AI 响应" 展示
8. **禁止**: 动态/流体/3D 背景效果

---

## 8. Implementation Priorities / 实现优先级

### P0 (MVP)
- [ ] 全局色彩变量设置
- [ ] 基础布局框架 (三栏)
- [ ] Header + Status Bar
- [ ] 左侧控制面板 (Query Input)
- [ ] 主 Canvas (静态框架)
- [ ] 右侧详情面板框架

### P1 (Core Features)
- [ ] 因果图节点渲染
- [ ] 辩论树组件
- [ ] 数据表格组件
- [ ] 基础交互 (点击、悬停)

### P2 (Enhanced)
- [ ] 动画过渡
- [ ] 响应式适配
- [ ] 键盘导航
