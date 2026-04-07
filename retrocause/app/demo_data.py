from __future__ import annotations

from retrocause.models import (
    AnalysisResult,
    CausalEdge,
    CausalVariable,
    CounterfactualResult,
    Evidence,
    EvidenceType,
    HypothesisChain,
    HypothesisStatus,
)

DEMO_EVIDENCES: list[Evidence] = [
    Evidence(
        id="ev1",
        content="Alvarez 等人 (1980) 在 K-Pg 界线发现铱异常，支持小行星撞击假说",
        source_type=EvidenceType.SCIENTIFIC,
        source_url="https://doi.org/10.1126/science.210.4471.1165",
        timestamp="1980-06-06",
        prior_reliability=0.95,
        posterior_reliability=0.97,
        linked_variables=["asteroid_impact", "k_pg_boundary"],
    ),
    Evidence(
        id="ev2",
        content="Chicxulub 陨石坑直径约 180km，年代与 K-Pg 界线吻合",
        source_type=EvidenceType.SCIENTIFIC,
        source_url="https://doi.org/10.1126/science.215.4539.1407",
        timestamp="1991-01-01",
        prior_reliability=0.93,
        posterior_reliability=0.96,
        linked_variables=["asteroid_impact", "chicxulub_crater"],
    ),
    Evidence(
        id="ev3",
        content="Deccan Traps 火山活动在 66Ma 前后持续约 75 万年",
        source_type=EvidenceType.LITERATURE,
        source_url="https://doi.org/10.1126/science.1179113",
        timestamp="2009-12-01",
        prior_reliability=0.85,
        posterior_reliability=0.82,
        linked_variables=["volcanic_activity", "climate_change"],
    ),
    Evidence(
        id="ev4",
        content="全球 K-Pg 界线地层中冲击石英和玻璃球粒的广泛分布",
        source_type=EvidenceType.DATA,
        timestamp="2010-03-15",
        prior_reliability=0.88,
        posterior_reliability=0.91,
        linked_variables=["asteroid_impact", "global_fire"],
    ),
    Evidence(
        id="ev5",
        content="海洋酸化导致钙质微体化石大规模灭绝的地球化学证据",
        source_type=EvidenceType.SCIENTIFIC,
        timestamp="2015-05-20",
        prior_reliability=0.80,
        posterior_reliability=0.84,
        linked_variables=["ocean_acidification", "marine_extinction"],
    ),
    Evidence(
        id="ev6",
        content="化石记录显示非鸟类恐龙在大约 66Ma 前突然消失",
        source_type=EvidenceType.ARCHIVE,
        timestamp="2020-01-10",
        prior_reliability=0.92,
        posterior_reliability=0.94,
        linked_variables=["dinosaur_extinction"],
    ),
    Evidence(
        id="ev7",
        content="气候模型显示撞击冬季可持续数年至数十年",
        source_type=EvidenceType.DATA,
        timestamp="2017-08-01",
        prior_reliability=0.78,
        posterior_reliability=0.81,
        linked_variables=["climate_change", "photosynthesis_shutdown"],
    ),
    Evidence(
        id="ev8",
        content="部分深海生物和淡水生物存活，支持食物链崩溃假说",
        source_type=EvidenceType.LITERATURE,
        timestamp="2016-11-05",
        prior_reliability=0.75,
        posterior_reliability=0.79,
        linked_variables=["food_chain_collapse", "marine_extinction"],
    ),
    Evidence(
        id="svb_ev1",
        content="美联储快速加息使长期债券市场价格显著回落。",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.82,
        linked_variables=["rate_hikes", "bond_losses"],
    ),
    Evidence(
        id="svb_ev2",
        content="SVB 资产端久期过长，对利率变动高度敏感。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.86,
        linked_variables=["rate_hikes", "bond_losses"],
    ),
    Evidence(
        id="svb_ev3",
        content="未实现亏损削弱市场对其资产负债表的信心。",
        source_type=EvidenceType.LITERATURE,
        posterior_reliability=0.78,
        linked_variables=["bond_losses", "confidence_shock"],
    ),
    Evidence(
        id="svb_ev4",
        content="SVB 储户结构集中在创投和科技企业，提现行为高度同步。",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.80,
        linked_variables=["deposit_concentration", "bank_run"],
    ),
    Evidence(
        id="svb_ev5",
        content="融资环境收紧导致客户现金消耗加快，进一步放大市场担忧。",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.74,
        linked_variables=["confidence_shock"],
    ),
    Evidence(
        id="svb_ev6",
        content="增发融资消息触发储户和投资者快速失去信心。",
        source_type=EvidenceType.TESTIMONY,
        posterior_reliability=0.73,
        linked_variables=["confidence_shock", "bank_run"],
    ),
    Evidence(
        id="svb_ev7",
        content="短时间内的大规模提款使流动性缺口迅速暴露。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.88,
        linked_variables=["bank_run", "svb_collapse"],
    ),
    Evidence(
        id="svb_ev8",
        content="监管接管发生在流动性危机无法自行修复之后。",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.84,
        linked_variables=["svb_collapse"],
    ),
    Evidence(
        id="stock_ev1",
        content="最新财报显示核心业务收入未达到市场预期。",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.81,
        linked_variables=["earnings_miss"],
    ),
    Evidence(
        id="stock_ev2",
        content="利润率下滑表明经营压力高于市场此前判断。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.84,
        linked_variables=["earnings_miss"],
    ),
    Evidence(
        id="stock_ev3",
        content="管理层在业绩说明会上下调了后续季度指引。",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.83,
        linked_variables=["guidance_cut"],
    ),
    Evidence(
        id="stock_ev4",
        content="板块资金流出导致同类高估值公司普遍承压。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.76,
        linked_variables=["sector_rotation"],
    ),
    Evidence(
        id="stock_ev5",
        content="市场舆论从增长放缓转向对公司长期故事失去信心。",
        source_type=EvidenceType.SOCIAL,
        posterior_reliability=0.68,
        linked_variables=["confidence_breakdown"],
    ),
    Evidence(
        id="stock_ev6",
        content="盘前与开盘阶段出现连续抛压，卖单主导成交。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.86,
        linked_variables=["confidence_breakdown", "stock_selloff"],
    ),
    Evidence(
        id="stock_ev7",
        content="量化与被动资金共同放大了下跌幅度。",
        source_type=EvidenceType.LITERATURE,
        posterior_reliability=0.71,
        linked_variables=["sector_rotation", "stock_selloff"],
    ),
    Evidence(
        id="stock_ev8",
        content="盘中跌破关键价位后触发更多止损与情绪性抛售。",
        source_type=EvidenceType.TESTIMONY,
        posterior_reliability=0.74,
        linked_variables=["stock_selloff"],
    ),
    Evidence(
        id="crisis_ev1",
        content="房地产贷款质量恶化削弱了抵押支持证券的价值。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.84,
        linked_variables=["housing_bubble", "toxic_mbs"],
    ),
    Evidence(
        id="crisis_ev2",
        content="宽松信贷标准扩大了高风险借款人的违约暴露。",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.80,
        linked_variables=["subprime_lending", "default_wave"],
    ),
    Evidence(
        id="crisis_ev3",
        content="证券化结构把风险分散并隐藏在复杂资产池之中。",
        source_type=EvidenceType.LITERATURE,
        posterior_reliability=0.78,
        linked_variables=["toxic_mbs", "banking_stress"],
    ),
    Evidence(
        id="crisis_ev4",
        content="高杠杆让金融机构难以承受资产价格快速下跌。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.87,
        linked_variables=["leverage", "banking_stress"],
    ),
    Evidence(
        id="crisis_ev5",
        content="违约率上升迅速冲击与住房相关的资产价值。",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.79,
        linked_variables=["default_wave", "toxic_mbs"],
    ),
    Evidence(
        id="crisis_ev6",
        content="同业市场冻结放大了流动性压力和系统性恐慌。",
        source_type=EvidenceType.TESTIMONY,
        posterior_reliability=0.75,
        linked_variables=["banking_stress", "credit_freeze"],
    ),
    Evidence(
        id="crisis_ev7",
        content="信用市场冻结向实体经济传导并导致全面危机。",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.82,
        linked_variables=["credit_freeze", "financial_crisis_2008"],
    ),
    Evidence(
        id="crisis_ev8",
        content="住房泡沫破裂是 2008 年金融危机的重要起点之一。",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.83,
        linked_variables=["housing_bubble", "financial_crisis_2008"],
    ),
    Evidence(
        id="rent_ev1",
        content="核心城市住房供给增长长期慢于人口与就业增长。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.86,
        linked_variables=["housing_supply_shortage", "rent_pressure"],
    ),
    Evidence(
        id="rent_ev2",
        content="分区与审批限制压缩了新住房建设速度。",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.79,
        linked_variables=["zoning_constraints", "housing_supply_shortage"],
    ),
    Evidence(
        id="rent_ev3",
        content="高收入就业机会集中抬升了核心区域住房支付能力。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.81,
        linked_variables=["income_demand", "rent_pressure"],
    ),
    Evidence(
        id="rent_ev4",
        content="短租和投资性持有在部分区域挤占了长期租赁供给。",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.71,
        linked_variables=["investor_pressure", "housing_supply_shortage"],
    ),
    Evidence(
        id="rent_ev5",
        content="利率和建材成本上升抬高了开发与持有成本。",
        source_type=EvidenceType.LITERATURE,
        posterior_reliability=0.73,
        linked_variables=["construction_costs", "rent_pressure"],
    ),
    Evidence(
        id="rent_ev6",
        content="供需缺口最终转化为租金持续上涨。",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.88,
        linked_variables=["rent_pressure", "high_rent"],
    ),
    Evidence(
        id="rent_ev7",
        content="城市间迁移与岗位集聚进一步推高热门区域租金。",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.74,
        linked_variables=["income_demand", "high_rent"],
    ),
    Evidence(
        id="rent_ev8",
        content="租客在短期内难以通过新增供给迅速获得缓冲。",
        source_type=EvidenceType.TESTIMONY,
        posterior_reliability=0.69,
        linked_variables=["high_rent"],
    ),
]


def detect_demo_topic(query: str) -> str | None:
    lowered = query.lower()

    if any(keyword in lowered for keyword in ["svb", "bank", "银行", "存款", "挤兑"]):
        return "svb"
    if any(keyword in lowered for keyword in ["股票", "股价", "stock", "shares", "暴跌"]):
        return "stock"
    if any(
        keyword in lowered
        for keyword in ["2008", "financial crisis", "金融危机", "次贷", "subprime"]
    ):
        return "crisis"
    if any(keyword in lowered for keyword in ["rent", "租金", "房租", "housing"]):
        return "rent"
    return None


def demo_result() -> AnalysisResult:
    variables = [
        CausalVariable(
            name="asteroid_impact",
            description="小行星撞击（Chicxulub）",
            evidence_ids=["ev1", "ev2", "ev4"],
            posterior_support=0.95,
            uncertainty_contribution=0.05,
        ),
        CausalVariable(
            name="volcanic_activity",
            description="Deccan Traps 大规模火山活动",
            evidence_ids=["ev3"],
            posterior_support=0.78,
            uncertainty_contribution=0.15,
        ),
        CausalVariable(
            name="climate_change",
            description="全球气候剧变（撞击冬季 + 火山冬天）",
            evidence_ids=["ev3", "ev7"],
            posterior_support=0.88,
            uncertainty_contribution=0.10,
        ),
        CausalVariable(
            name="food_chain_collapse",
            description="全球食物链崩溃",
            evidence_ids=["ev7", "ev8"],
            posterior_support=0.82,
            uncertainty_contribution=0.12,
        ),
        CausalVariable(
            name="dinosaur_extinction",
            description="非鸟类恐龙大规模灭绝",
            evidence_ids=["ev6"],
            posterior_support=0.97,
            uncertainty_contribution=0.03,
        ),
    ]

    edges = [
        CausalEdge(
            source="asteroid_impact",
            target="climate_change",
            conditional_prob=0.90,
            confidence_interval=(0.82, 0.96),
            supporting_evidence_ids=["ev1", "ev4", "ev7"],
            refuting_evidence_ids=[],
        ),
        CausalEdge(
            source="volcanic_activity",
            target="climate_change",
            conditional_prob=0.65,
            confidence_interval=(0.50, 0.80),
            supporting_evidence_ids=["ev3"],
            refuting_evidence_ids=[],
        ),
        CausalEdge(
            source="climate_change",
            target="food_chain_collapse",
            conditional_prob=0.85,
            confidence_interval=(0.75, 0.93),
            supporting_evidence_ids=["ev7", "ev8"],
            refuting_evidence_ids=[],
        ),
        CausalEdge(
            source="food_chain_collapse",
            target="dinosaur_extinction",
            conditional_prob=0.92,
            confidence_interval=(0.85, 0.97),
            supporting_evidence_ids=["ev6", "ev8"],
            refuting_evidence_ids=[],
        ),
        CausalEdge(
            source="asteroid_impact",
            target="dinosaur_extinction",
            conditional_prob=0.15,
            confidence_interval=(0.05, 0.30),
            supporting_evidence_ids=[],
            refuting_evidence_ids=["ev6"],
        ),
    ]

    h1 = HypothesisChain(
        id="h1",
        name="小行星撞击主导假说",
        description="Chicxulub 小行星撞击引发的连锁反应导致恐龙灭绝",
        variables=[variables[0], variables[2], variables[3], variables[4]],
        edges=[edges[0], edges[2], edges[3]],
        path_probability=0.70,
        posterior_probability=0.78,
        confidence_interval=(0.68, 0.87),
        status=HypothesisStatus.REFINED,
        debate_rounds=[
            {
                "round": 1,
                "abductive": "铱异常和冲击石英的全球分布强烈指向撞击事件",
                "deductive": "若撞击发生，则必产生全球性气候灾难",
                "inductive": "多次生物大灭绝与撞击事件相关",
                "devil_advocate": "火山活动可能是共因而非替代解释",
                "arbitrator": "倾向于撞击主导，火山为辅助因素",
            },
            {
                "round": 2,
                "abductive": "时间分辨率提升后，撞击与灭绝时间精确吻合",
                "deductive": "食物链从底层崩溃可解释选择性灭绝模式",
                "inductive": "淡水生物高存活率支持短期灾难而非长期气候变暖",
                "devil_advocate": "仍不能完全排除火山作为主要压力源",
                "arbitrator": "维持撞击主导判断，置信度上调",
            },
        ],
        evidence_coverage=0.85,
        unanchored_edges=[],
        counterfactual_results=[
            CounterfactualResult(
                hypothesis_id="h1",
                intervention_var="asteroid_impact",
                original_path_prob=0.70,
                intervened_path_prob=0.08,
                probability_delta=-0.62,
                still_reachable=False,
                sensitivity_lower=0.03,
                sensitivity_upper=0.12,
                counterfactual_score=0.88,
            ),
            CounterfactualResult(
                hypothesis_id="h1",
                intervention_var="climate_change",
                original_path_prob=0.70,
                intervened_path_prob=0.12,
                probability_delta=-0.58,
                still_reachable=False,
                sensitivity_lower=0.05,
                sensitivity_upper=0.18,
                counterfactual_score=0.83,
            ),
        ],
        counterfactual_score=0.86,
    )

    h2 = HypothesisChain(
        id="h2",
        name="火山活动主导假说",
        description="Deccan Traps 持续火山活动通过温室效应和海洋酸化导致灭绝",
        variables=[variables[1], variables[2], variables[3], variables[4]],
        edges=[edges[1], edges[2], edges[3]],
        path_probability=0.35,
        posterior_probability=0.42,
        confidence_interval=(0.28, 0.56),
        status=HypothesisStatus.ACTIVE,
        debate_rounds=[
            {
                "round": 1,
                "abductive": "Deccan Traps 时间跨度覆盖灭绝期",
                "deductive": "长期排放可导致渐进式气候变化",
                "inductive": "其他大灭绝事件（如 P-Tr）与火山活动相关",
                "devil_advocate": "时间分辨率不足以建立因果关系",
                "arbitrator": "火山活动作为辅助因素成立，但主导性证据不足",
            },
        ],
        evidence_coverage=0.55,
        unanchored_edges=["volcanic_activity -> food_chain_collapse"],
        counterfactual_results=[
            CounterfactualResult(
                hypothesis_id="h2",
                intervention_var="volcanic_activity",
                original_path_prob=0.35,
                intervened_path_prob=0.18,
                probability_delta=-0.17,
                still_reachable=True,
                sensitivity_lower=0.10,
                sensitivity_upper=0.30,
                counterfactual_score=0.49,
            ),
        ],
        counterfactual_score=0.49,
    )

    return AnalysisResult(
        query="恐龙为什么灭绝？",
        domain="paleontology",
        variables=variables,
        edges=edges,
        hypotheses=[h1, h2],
        total_evidence_count=len(DEMO_EVIDENCES),
        total_uncertainty=0.12,
        recommended_next_steps=[
            "获取更高分辨率的放射性定年数据",
            "分析更多 K-Pg 界线的生物标志物",
            "运行多因素耦合的气候-生态模型",
        ],
        is_demo=True,
        demo_topic="default",
    )


def topic_aware_demo_result(query: str) -> AnalysisResult:
    topic = detect_demo_topic(query)

    if topic == "svb":
        variables = [
            CausalVariable(
                name="rate_hikes",
                description="持续加息导致长期债券价格下跌",
                evidence_ids=["svb_ev1", "svb_ev2"],
                posterior_support=0.86,
                uncertainty_contribution=0.10,
            ),
            CausalVariable(
                name="bond_losses",
                description="持有至到期资产形成大额浮亏",
                evidence_ids=["svb_ev2", "svb_ev3"],
                posterior_support=0.84,
                uncertainty_contribution=0.11,
            ),
            CausalVariable(
                name="deposit_concentration",
                description="储户高度集中于风险敏感的科技创投群体",
                evidence_ids=["svb_ev4"],
                posterior_support=0.80,
                uncertainty_contribution=0.13,
            ),
            CausalVariable(
                name="confidence_shock",
                description="融资环境恶化与融资消息引发信心冲击",
                evidence_ids=["svb_ev5", "svb_ev6"],
                posterior_support=0.82,
                uncertainty_contribution=0.12,
            ),
            CausalVariable(
                name="bank_run",
                description="大规模集中提取存款导致流动性危机",
                evidence_ids=["svb_ev6", "svb_ev7"],
                posterior_support=0.91,
                uncertainty_contribution=0.08,
            ),
            CausalVariable(
                name="svb_collapse",
                description="SVB 快速失去流动性并被监管接管",
                evidence_ids=["svb_ev7", "svb_ev8"],
                posterior_support=0.95,
                uncertainty_contribution=0.05,
            ),
        ]

        edges = [
            CausalEdge(
                source="rate_hikes",
                target="bond_losses",
                conditional_prob=0.88,
                confidence_interval=(0.78, 0.94),
                supporting_evidence_ids=["svb_ev1", "svb_ev2", "svb_ev3"],
            ),
            CausalEdge(
                source="bond_losses",
                target="confidence_shock",
                conditional_prob=0.76,
                confidence_interval=(0.64, 0.86),
                supporting_evidence_ids=["svb_ev3", "svb_ev5"],
            ),
            CausalEdge(
                source="deposit_concentration",
                target="bank_run",
                conditional_prob=0.79,
                confidence_interval=(0.66, 0.88),
                supporting_evidence_ids=["svb_ev4", "svb_ev6"],
            ),
            CausalEdge(
                source="confidence_shock",
                target="bank_run",
                conditional_prob=0.87,
                confidence_interval=(0.77, 0.93),
                supporting_evidence_ids=["svb_ev5", "svb_ev6", "svb_ev7"],
            ),
            CausalEdge(
                source="bank_run",
                target="svb_collapse",
                conditional_prob=0.94,
                confidence_interval=(0.86, 0.98),
                supporting_evidence_ids=["svb_ev7", "svb_ev8"],
            ),
        ]

        hypothesis = HypothesisChain(
            id="demo_svb_primary",
            name="SVB 流动性挤兑主导假说",
            description="加息导致资产浮亏，叠加储户集中与信心冲击，最终演化为银行挤兑并触发接管。",
            variables=variables,
            edges=edges,
            path_probability=0.67,
            posterior_probability=0.76,
            confidence_interval=(0.65, 0.85),
            status=HypothesisStatus.REFINED,
            evidence_coverage=0.81,
            unanchored_edges=[],
            counterfactual_results=[
                CounterfactualResult(
                    hypothesis_id="demo_svb_primary",
                    intervention_var="confidence_shock",
                    original_path_prob=0.67,
                    intervened_path_prob=0.22,
                    probability_delta=-0.45,
                    still_reachable=True,
                    sensitivity_lower=0.16,
                    sensitivity_upper=0.31,
                    counterfactual_score=0.72,
                )
            ],
            counterfactual_score=0.72,
        )

        return AnalysisResult(
            query=query,
            domain="finance",
            variables=variables,
            edges=edges,
            hypotheses=[hypothesis],
            total_evidence_count=8,
            total_uncertainty=0.14,
            recommended_next_steps=[
                "接入真实金融新闻与监管披露数据源",
                "补充利率路径与资产久期敏感性分析",
                "比较储户结构与挤兑速度对结果的影响",
            ],
            is_demo=True,
            demo_topic="svb",
        )

    if topic == "stock":
        variables = [
            CausalVariable(
                name="earnings_miss",
                description="业绩不及预期削弱市场对公司基本面的信心",
                evidence_ids=["stock_ev1", "stock_ev2"],
                posterior_support=0.84,
                uncertainty_contribution=0.11,
            ),
            CausalVariable(
                name="guidance_cut",
                description="公司下调未来指引，放大悲观预期",
                evidence_ids=["stock_ev3"],
                posterior_support=0.79,
                uncertainty_contribution=0.13,
            ),
            CausalVariable(
                name="sector_rotation",
                description="行业资金轮动导致高估值标的被抛售",
                evidence_ids=["stock_ev4"],
                posterior_support=0.72,
                uncertainty_contribution=0.14,
            ),
            CausalVariable(
                name="confidence_breakdown",
                description="多重利空叠加造成投资者信心快速崩塌",
                evidence_ids=["stock_ev5", "stock_ev6"],
                posterior_support=0.83,
                uncertainty_contribution=0.10,
            ),
            CausalVariable(
                name="stock_selloff",
                description="抛售压力集中释放，股价快速下跌",
                evidence_ids=["stock_ev6", "stock_ev7", "stock_ev8"],
                posterior_support=0.92,
                uncertainty_contribution=0.07,
            ),
        ]

        edges = [
            CausalEdge(
                source="earnings_miss",
                target="confidence_breakdown",
                conditional_prob=0.82,
                confidence_interval=(0.70, 0.90),
                supporting_evidence_ids=["stock_ev1", "stock_ev2", "stock_ev5"],
            ),
            CausalEdge(
                source="guidance_cut",
                target="confidence_breakdown",
                conditional_prob=0.78,
                confidence_interval=(0.66, 0.88),
                supporting_evidence_ids=["stock_ev3", "stock_ev5"],
            ),
            CausalEdge(
                source="sector_rotation",
                target="stock_selloff",
                conditional_prob=0.64,
                confidence_interval=(0.50, 0.77),
                supporting_evidence_ids=["stock_ev4", "stock_ev7"],
            ),
            CausalEdge(
                source="confidence_breakdown",
                target="stock_selloff",
                conditional_prob=0.89,
                confidence_interval=(0.80, 0.95),
                supporting_evidence_ids=["stock_ev5", "stock_ev6", "stock_ev8"],
            ),
        ]

        hypothesis = HypothesisChain(
            id="demo_stock_primary",
            name="业绩失速与信心崩塌主导假说",
            description="业绩不及预期与指引下调共同打击投资者信心，再叠加板块轮动，最终触发股价暴跌。",
            variables=variables,
            edges=edges,
            path_probability=0.63,
            posterior_probability=0.74,
            confidence_interval=(0.60, 0.83),
            status=HypothesisStatus.REFINED,
            evidence_coverage=0.78,
            unanchored_edges=[],
            counterfactual_results=[
                CounterfactualResult(
                    hypothesis_id="demo_stock_primary",
                    intervention_var="guidance_cut",
                    original_path_prob=0.63,
                    intervened_path_prob=0.35,
                    probability_delta=-0.28,
                    still_reachable=True,
                    sensitivity_lower=0.24,
                    sensitivity_upper=0.43,
                    counterfactual_score=0.64,
                )
            ],
            counterfactual_score=0.64,
        )

        return AnalysisResult(
            query=query,
            domain="finance",
            variables=variables,
            edges=edges,
            hypotheses=[hypothesis],
            total_evidence_count=8,
            total_uncertainty=0.16,
            recommended_next_steps=[
                "接入真实财报与市场行情数据源",
                "比较业绩因素与市场风格轮动的相对贡献",
                "加入事件时间线以区分盘前与盘中冲击",
            ],
            is_demo=True,
            demo_topic="stock",
        )

    if topic == "crisis":
        variables = [
            CausalVariable(
                "housing_bubble", "住房泡沫积累并反转", ["crisis_ev1", "crisis_ev8"], 0.86, 0.11
            ),
            CausalVariable(
                "subprime_lending", "次贷扩张放大了脆弱借款人的违约风险", ["crisis_ev2"], 0.82, 0.12
            ),
            CausalVariable(
                "toxic_mbs",
                "证券化资产中累积了难以识别的住房风险",
                ["crisis_ev1", "crisis_ev3", "crisis_ev5"],
                0.84,
                0.10,
            ),
            CausalVariable(
                "leverage", "高杠杆放大了资产价格下跌的冲击", ["crisis_ev4"], 0.80, 0.13
            ),
            CausalVariable(
                "banking_stress",
                "金融机构承压并失去流动性缓冲",
                ["crisis_ev3", "crisis_ev4", "crisis_ev6"],
                0.87,
                0.09,
            ),
            CausalVariable(
                "credit_freeze", "同业和信用市场冻结", ["crisis_ev6", "crisis_ev7"], 0.89, 0.08
            ),
            CausalVariable(
                "financial_crisis_2008",
                "2008 年金融危机全面爆发",
                ["crisis_ev7", "crisis_ev8"],
                0.94,
                0.06,
            ),
        ]
        edges = [
            CausalEdge(
                "housing_bubble", "toxic_mbs", 0.83, (0.72, 0.91), ["crisis_ev1", "crisis_ev8"]
            ),
            CausalEdge(
                "subprime_lending", "toxic_mbs", 0.79, (0.66, 0.88), ["crisis_ev2", "crisis_ev5"]
            ),
            CausalEdge(
                "toxic_mbs", "banking_stress", 0.85, (0.74, 0.92), ["crisis_ev3", "crisis_ev5"]
            ),
            CausalEdge("leverage", "banking_stress", 0.81, (0.68, 0.90), ["crisis_ev4"]),
            CausalEdge("banking_stress", "credit_freeze", 0.88, (0.79, 0.94), ["crisis_ev6"]),
            CausalEdge(
                "credit_freeze", "financial_crisis_2008", 0.92, (0.84, 0.97), ["crisis_ev7"]
            ),
        ]
        hypothesis = HypothesisChain(
            id="demo_crisis_primary",
            name="住房泡沫与杠杆失衡主导假说",
            description="住房泡沫、次贷扩张和高杠杆共同累积风险，最终通过信用冻结演化为 2008 金融危机。",
            variables=variables,
            edges=edges,
            path_probability=0.66,
            posterior_probability=0.77,
            confidence_interval=(0.66, 0.86),
            status=HypothesisStatus.REFINED,
            evidence_coverage=0.82,
            unanchored_edges=[],
            counterfactual_results=[
                CounterfactualResult(
                    "demo_crisis_primary", "leverage", 0.66, 0.33, -0.33, True, 0.24, 0.42, 0.69
                )
            ],
            counterfactual_score=0.69,
        )
        return AnalysisResult(
            query=query,
            domain="finance",
            variables=variables,
            edges=edges,
            hypotheses=[hypothesis],
            total_evidence_count=8,
            total_uncertainty=0.15,
            recommended_next_steps=[
                "接入住房价格与违约率的真实时序数据",
                "比较杠杆与证券化结构的相对贡献",
                "补充监管与流动性事件时间线",
            ],
            is_demo=True,
            demo_topic="crisis",
        )

    if topic == "rent":
        variables = [
            CausalVariable(
                "zoning_constraints", "分区与审批限制压缩新房供给速度", ["rent_ev2"], 0.78, 0.13
            ),
            CausalVariable(
                "investor_pressure", "投资性持有与短租挤占长期供给", ["rent_ev4"], 0.70, 0.15
            ),
            CausalVariable(
                "housing_supply_shortage",
                "住房供给长期不足",
                ["rent_ev1", "rent_ev2", "rent_ev4"],
                0.87,
                0.09,
            ),
            CausalVariable(
                "income_demand",
                "高收入岗位与人口集聚推高支付能力",
                ["rent_ev3", "rent_ev7"],
                0.81,
                0.11,
            ),
            CausalVariable("construction_costs", "开发与持有成本上升", ["rent_ev5"], 0.72, 0.14),
            CausalVariable(
                "rent_pressure",
                "供需与成本共同形成租金上行压力",
                ["rent_ev1", "rent_ev3", "rent_ev5", "rent_ev6"],
                0.88,
                0.08,
            ),
            CausalVariable(
                "high_rent", "租金长期维持高位", ["rent_ev6", "rent_ev7", "rent_ev8"], 0.93, 0.06
            ),
        ]
        edges = [
            CausalEdge(
                "zoning_constraints", "housing_supply_shortage", 0.82, (0.69, 0.90), ["rent_ev2"]
            ),
            CausalEdge(
                "investor_pressure", "housing_supply_shortage", 0.66, (0.52, 0.79), ["rent_ev4"]
            ),
            CausalEdge(
                "housing_supply_shortage",
                "rent_pressure",
                0.89,
                (0.80, 0.95),
                ["rent_ev1", "rent_ev6"],
            ),
            CausalEdge(
                "income_demand", "rent_pressure", 0.77, (0.64, 0.87), ["rent_ev3", "rent_ev7"]
            ),
            CausalEdge("construction_costs", "rent_pressure", 0.63, (0.49, 0.76), ["rent_ev5"]),
            CausalEdge("rent_pressure", "high_rent", 0.93, (0.85, 0.97), ["rent_ev6", "rent_ev8"]),
        ]
        hypothesis = HypothesisChain(
            id="demo_rent_primary",
            name="供给约束与需求集聚主导假说",
            description="住房供给受限、需求集中和成本上升共同作用，导致核心区域租金长期高企。",
            variables=variables,
            edges=edges,
            path_probability=0.68,
            posterior_probability=0.79,
            confidence_interval=(0.68, 0.87),
            status=HypothesisStatus.REFINED,
            evidence_coverage=0.80,
            unanchored_edges=[],
            counterfactual_results=[
                CounterfactualResult(
                    "demo_rent_primary",
                    "housing_supply_shortage",
                    0.68,
                    0.29,
                    -0.39,
                    True,
                    0.19,
                    0.37,
                    0.71,
                )
            ],
            counterfactual_score=0.71,
        )
        return AnalysisResult(
            query=query,
            domain="economics",
            variables=variables,
            edges=edges,
            hypotheses=[hypothesis],
            total_evidence_count=8,
            total_uncertainty=0.16,
            recommended_next_steps=[
                "接入城市级供给与租金时间序列",
                "比较分区限制与成本因素的边际影响",
                "引入人口迁移与就业集聚的细粒度数据",
            ],
            is_demo=True,
            demo_topic="rent",
        )

    result = demo_result()
    result.query = query
    result.is_demo = True
    result.demo_topic = "default"
    return result


PROVIDERS: dict[str, dict] = {
    "openrouter": {
        "label": "OpenRouter（多模型中转）",
        "base_url": "https://openrouter.ai/api/v1",
        "models": {
            "deepseek/deepseek-chat-v3-0324": "DeepSeek V3（推荐，性价比高）",
            "deepseek/deepseek-r1": "DeepSeek R1",
            "google/gemini-2.0-flash-001": "Gemini 2.0 Flash（快速）",
            "anthropic/claude-sonnet-4": "Claude Sonnet 4",
            "openai/gpt-4o-mini": "GPT-4o Mini",
            "meta-llama/llama-4-maverick": "Llama 4 Maverick",
            "qwen/qwen3-235b-a22b": "Qwen3 235B",
            "mistralai/mistral-small-3.1-24b-instruct": "Mistral Small 3.1",
            "moonshotai/kimi-k2": "Kimi K2",
            "zhipuai/glm-4.5": "GLM 4.5",
        },
    },
    "openai": {
        "label": "OpenAI（直连）",
        "base_url": None,
        "models": {
            "gpt-4o-mini": "GPT-4o Mini（直连）",
            "gpt-4o": "GPT-4o（直连）",
        },
    },
    "dashscope": {
        "label": "DashScope / 阿里百炼（官方）",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": {
            "qwen-max": "Qwen Max",
            "qwen-plus": "Qwen Plus",
            "qwen-turbo": "Qwen Turbo",
            "qwen-long": "Qwen Long",
        },
    },
    "zhipu": {
        "label": "Zhipu / 智谱（官方）",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "models": {
            "glm-4.5": "GLM 4.5",
            "glm-4.5-air": "GLM 4.5 Air",
            "glm-4-air": "GLM 4 Air",
        },
    },
    "moonshot": {
        "label": "Moonshot / Kimi（官方）",
        "base_url": "https://api.moonshot.cn/v1",
        "models": {
            "moonshot-v1-8k": "Moonshot 8K",
            "moonshot-v1-32k": "Moonshot 32K",
            "moonshot-v1-128k": "Moonshot 128K",
        },
    },
    "deepseek": {
        "label": "DeepSeek（官方）",
        "base_url": "https://api.deepseek.com/v1",
        "models": {
            "deepseek-chat": "DeepSeek Chat",
            "deepseek-reasoner": "DeepSeek Reasoner",
        },
    },
}


def run_real_analysis(
    query: str, api_key: str, model: str, base_url: str | None
) -> AnalysisResult | None:
    from retrocause.config import RetroCauseConfig as _Config
    from retrocause.engine import analyze as _analyze
    from retrocause.llm import LLMClient as _LLMClient
    from retrocause.sources.arxiv import ArxivSourceAdapter as _Arxiv
    from retrocause.sources.semantic_scholar import SemanticScholarAdapter as _SS
    from retrocause.sources.web import WebSearchAdapter as _Web

    cfg = _Config.from_env()
    llm = _LLMClient(
        api_key=api_key, model=model, base_url=base_url, timeout=cfg.request_timeout_seconds
    )
    sources = [_Arxiv(), _SS(), _Web()]
    return _analyze(query, llm_client=llm, source_adapters=sources, config=cfg)
