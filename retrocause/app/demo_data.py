from __future__ import annotations

from collections.abc import Callable

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
        content="Alvarez et al. (1980) found an iridium anomaly at the K-Pg boundary, supporting the asteroid-impact hypothesis.",
        source_type=EvidenceType.SCIENTIFIC,
        source_url="https://doi.org/10.1126/science.210.4471.1165",
        timestamp="1980-06-06",
        prior_reliability=0.95,
        posterior_reliability=0.97,
        linked_variables=["asteroid_impact", "k_pg_boundary"],
    ),
    Evidence(
        id="ev2",
        content="The Chicxulub crater is about 180 km wide and dates to the K-Pg boundary interval.",
        source_type=EvidenceType.SCIENTIFIC,
        source_url="https://doi.org/10.1126/science.215.4539.1407",
        timestamp="1991-01-01",
        prior_reliability=0.93,
        posterior_reliability=0.96,
        linked_variables=["asteroid_impact", "chicxulub_crater"],
    ),
    Evidence(
        id="ev3",
        content="Deccan Traps volcanism remained active across the interval around 66 Ma for roughly 750,000 years.",
        source_type=EvidenceType.LITERATURE,
        source_url="https://doi.org/10.1126/science.1179113",
        timestamp="2009-12-01",
        prior_reliability=0.85,
        posterior_reliability=0.82,
        linked_variables=["volcanic_activity", "climate_change"],
    ),
    Evidence(
        id="ev4",
        content="Shock quartz and glass spherules are distributed widely in K-Pg boundary layers around the world.",
        source_type=EvidenceType.DATA,
        timestamp="2010-03-15",
        prior_reliability=0.88,
        posterior_reliability=0.91,
        linked_variables=["asteroid_impact", "global_fire"],
    ),
    Evidence(
        id="ev5",
        content="Geochemical evidence points to ocean acidification contributing to large-scale loss of calcareous microfossils.",
        source_type=EvidenceType.SCIENTIFIC,
        timestamp="2015-05-20",
        prior_reliability=0.80,
        posterior_reliability=0.84,
        linked_variables=["ocean_acidification", "marine_extinction"],
    ),
    Evidence(
        id="ev6",
        content="The fossil record shows non-avian dinosaurs disappearing abruptly around 66 Ma.",
        source_type=EvidenceType.ARCHIVE,
        timestamp="2020-01-10",
        prior_reliability=0.92,
        posterior_reliability=0.94,
        linked_variables=["dinosaur_extinction"],
    ),
    Evidence(
        id="ev7",
        content="Climate models suggest an impact winter could have lasted from several years to multiple decades.",
        source_type=EvidenceType.DATA,
        timestamp="2017-08-01",
        prior_reliability=0.78,
        posterior_reliability=0.81,
        linked_variables=["climate_change", "photosynthesis_shutdown"],
    ),
    Evidence(
        id="ev8",
        content="Some deep-sea and freshwater species survived, supporting a food-chain collapse scenario rather than uniform extinction pressure.",
        source_type=EvidenceType.LITERATURE,
        timestamp="2016-11-05",
        prior_reliability=0.75,
        posterior_reliability=0.79,
        linked_variables=["food_chain_collapse", "marine_extinction"],
    ),
    Evidence(
        id="svb_ev1",
        content="Rapid Fed rate hikes sharply reduced the market value of long-duration bonds.",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.82,
        linked_variables=["rate_hikes", "bond_losses"],
    ),
    Evidence(
        id="svb_ev2",
        content="SVB carried unusually long-duration assets, making it highly sensitive to rate moves.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.86,
        linked_variables=["rate_hikes", "bond_losses"],
    ),
    Evidence(
        id="svb_ev3",
        content="Unrealized losses weakened market confidence in the bank's balance sheet.",
        source_type=EvidenceType.LITERATURE,
        posterior_reliability=0.78,
        linked_variables=["bond_losses", "confidence_shock"],
    ),
    Evidence(
        id="svb_ev4",
        content="SVB's deposit base was concentrated in venture and technology clients, increasing synchronized withdrawals.",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.80,
        linked_variables=["deposit_concentration", "bank_run"],
    ),
    Evidence(
        id="svb_ev5",
        content="Tighter funding conditions accelerated client cash burn and amplified market concern.",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.74,
        linked_variables=["confidence_shock"],
    ),
    Evidence(
        id="svb_ev6",
        content="The capital-raise announcement triggered a rapid loss of depositor and investor confidence.",
        source_type=EvidenceType.TESTIMONY,
        posterior_reliability=0.73,
        linked_variables=["confidence_shock", "bank_run"],
    ),
    Evidence(
        id="svb_ev7",
        content="Large withdrawals in a short time exposed the liquidity gap almost immediately.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.88,
        linked_variables=["bank_run", "svb_collapse"],
    ),
    Evidence(
        id="svb_ev8",
        content="Regulators stepped in only after the liquidity crisis could no longer be repaired internally.",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.84,
        linked_variables=["svb_collapse"],
    ),
    Evidence(
        id="stock_ev1",
        content="The latest earnings report showed core revenue missing market expectations.",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.81,
        linked_variables=["earnings_miss"],
    ),
    Evidence(
        id="stock_ev2",
        content="Shrinking margins signaled heavier operating pressure than the market had assumed.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.84,
        linked_variables=["earnings_miss"],
    ),
    Evidence(
        id="stock_ev3",
        content="Management lowered forward guidance during the earnings call.",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.83,
        linked_variables=["guidance_cut"],
    ),
    Evidence(
        id="stock_ev4",
        content="Sector outflows pushed comparable high-multiple stocks lower as well.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.76,
        linked_variables=["sector_rotation"],
    ),
    Evidence(
        id="stock_ev5",
        content="Market narrative shifted from slowing growth to losing confidence in the long-term company story.",
        source_type=EvidenceType.SOCIAL,
        posterior_reliability=0.68,
        linked_variables=["confidence_breakdown"],
    ),
    Evidence(
        id="stock_ev6",
        content="Pre-market and opening-session selling pressure dominated trading.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.86,
        linked_variables=["confidence_breakdown", "stock_selloff"],
    ),
    Evidence(
        id="stock_ev7",
        content="Quant and passive flows amplified the magnitude of the decline.",
        source_type=EvidenceType.LITERATURE,
        posterior_reliability=0.71,
        linked_variables=["sector_rotation", "stock_selloff"],
    ),
    Evidence(
        id="stock_ev8",
        content="Breaking key price levels intraday triggered more stops and emotional selling.",
        source_type=EvidenceType.TESTIMONY,
        posterior_reliability=0.74,
        linked_variables=["stock_selloff"],
    ),
    Evidence(
        id="crisis_ev1",
        content="Deteriorating mortgage quality weakened the value of mortgage-backed securities.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.84,
        linked_variables=["housing_bubble", "toxic_mbs"],
    ),
    Evidence(
        id="crisis_ev2",
        content="Loose underwriting standards expanded default exposure among high-risk borrowers.",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.80,
        linked_variables=["subprime_lending", "default_wave"],
    ),
    Evidence(
        id="crisis_ev3",
        content="Securitization spread and obscured risk inside complex asset pools.",
        source_type=EvidenceType.LITERATURE,
        posterior_reliability=0.78,
        linked_variables=["toxic_mbs", "banking_stress"],
    ),
    Evidence(
        id="crisis_ev4",
        content="High leverage left financial institutions unable to absorb rapid asset-price declines.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.87,
        linked_variables=["leverage", "banking_stress"],
    ),
    Evidence(
        id="crisis_ev5",
        content="Rising defaults quickly hit the value of housing-linked assets.",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.79,
        linked_variables=["default_wave", "toxic_mbs"],
    ),
    Evidence(
        id="crisis_ev6",
        content="Interbank market freezes intensified liquidity stress and systemic panic.",
        source_type=EvidenceType.TESTIMONY,
        posterior_reliability=0.75,
        linked_variables=["banking_stress", "credit_freeze"],
    ),
    Evidence(
        id="crisis_ev7",
        content="Credit-market freezes spread into the real economy and turned stress into a full crisis.",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.82,
        linked_variables=["credit_freeze", "financial_crisis_2008"],
    ),
    Evidence(
        id="crisis_ev8",
        content="The housing-bubble collapse was one of the central starting points of the 2008 financial crisis.",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.83,
        linked_variables=["housing_bubble", "financial_crisis_2008"],
    ),
    Evidence(
        id="rent_ev1",
        content="Core-city housing supply has grown more slowly than population and job growth for years.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.86,
        linked_variables=["housing_supply_shortage", "rent_pressure"],
    ),
    Evidence(
        id="rent_ev2",
        content="Zoning and permitting limits have constrained the pace of new housing construction.",
        source_type=EvidenceType.ARCHIVE,
        posterior_reliability=0.79,
        linked_variables=["zoning_constraints", "housing_supply_shortage"],
    ),
    Evidence(
        id="rent_ev3",
        content="High-income job concentration has raised willingness and ability to pay in core neighborhoods.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.81,
        linked_variables=["income_demand", "rent_pressure"],
    ),
    Evidence(
        id="rent_ev4",
        content="Short-term rentals and investor ownership have displaced some long-term rental supply.",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.71,
        linked_variables=["investor_pressure", "housing_supply_shortage"],
    ),
    Evidence(
        id="rent_ev5",
        content="Higher rates and material costs have raised development and holding costs.",
        source_type=EvidenceType.LITERATURE,
        posterior_reliability=0.73,
        linked_variables=["construction_costs", "rent_pressure"],
    ),
    Evidence(
        id="rent_ev6",
        content="The supply-demand gap has ultimately translated into persistent rent pressure.",
        source_type=EvidenceType.DATA,
        posterior_reliability=0.88,
        linked_variables=["rent_pressure", "high_rent"],
    ),
    Evidence(
        id="rent_ev7",
        content="Migration between cities and job clustering have pushed hot urban rents even higher.",
        source_type=EvidenceType.NEWS,
        posterior_reliability=0.74,
        linked_variables=["income_demand", "high_rent"],
    ),
    Evidence(
        id="rent_ev8",
        content="Renters usually cannot get fast relief from new supply in the short run.",
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
            description="Asteroid impact near Chicxulub.",
            evidence_ids=["ev1", "ev2", "ev4"],
            posterior_support=0.95,
            uncertainty_contribution=0.05,
        ),
        CausalVariable(
            name="volcanic_activity",
            description="Large-scale Deccan Traps volcanism.",
            evidence_ids=["ev3"],
            posterior_support=0.78,
            uncertainty_contribution=0.15,
        ),
        CausalVariable(
            name="climate_change",
            description="Abrupt global climate shock after the impact and volcanism.",
            evidence_ids=["ev3", "ev7"],
            posterior_support=0.88,
            uncertainty_contribution=0.10,
        ),
        CausalVariable(
            name="food_chain_collapse",
            description="Collapse of major food webs.",
            evidence_ids=["ev7", "ev8"],
            posterior_support=0.82,
            uncertainty_contribution=0.12,
        ),
        CausalVariable(
            name="dinosaur_extinction",
            description="Mass extinction of non-avian dinosaurs.",
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
        name="Asteroid-led extinction hypothesis",
        description="A Chicxulub impact triggered cascading climate and food-chain stress that drove dinosaur extinction.",
        variables=[variables[0], variables[2], variables[3], variables[4]],
        edges=[edges[0], edges[2], edges[3]],
        path_probability=0.70,
        posterior_probability=0.78,
        confidence_interval=(0.68, 0.87),
        status=HypothesisStatus.REFINED,
        debate_rounds=[
            {
                "round": 1,
                "abductive": "Global iridium and impact markers point strongly toward a large collision event.",
                "deductive": "If a major impact occurred, a severe short-term climate shock should follow.",
                "inductive": "Multiple extinction patterns are consistent with a rapid collapse after impact.",
                "devil_advocate": "Volcanism might still explain some of the same signatures.",
                "arbitrator": "Impact remains the leading cause, with volcanism as a secondary contributor.",
            },
            {
                "round": 2,
                "abductive": "Improved dating aligns impact timing closely with the extinction boundary.",
                "deductive": "Food-web collapse explains selective survival better than a slow uniform decline.",
                "inductive": "Freshwater survival patterns fit a short intense disruption.",
                "devil_advocate": "Volcanism still contributes background stress and uncertainty.",
                "arbitrator": "The impact-led story remains strongest after the second pass.",
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
        name="Volcanism-led extinction hypothesis",
        description="Persistent Deccan Traps volcanism drove climate and ocean stress that contributed materially to extinction.",
        variables=[variables[1], variables[2], variables[3], variables[4]],
        edges=[edges[1], edges[2], edges[3]],
        path_probability=0.35,
        posterior_probability=0.42,
        confidence_interval=(0.28, 0.56),
        status=HypothesisStatus.ACTIVE,
        debate_rounds=[
            {
                "round": 1,
                "abductive": "Volcanism overlaps the extinction interval and could explain sustained stress.",
                "deductive": "Long emissions would be expected to alter climate and ocean chemistry.",
                "inductive": "Other extinction episodes also correlate with major volcanism.",
                "devil_advocate": "Dating precision is weaker than the impact case.",
                "arbitrator": "Volcanism remains plausible but less well supported as the main cause.",
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
        query="Why did dinosaurs go extinct?",
        domain="paleontology",
        variables=variables,
        edges=edges,
        hypotheses=[h1, h2],
        total_evidence_count=len(DEMO_EVIDENCES),
        total_uncertainty=0.12,
        recommended_next_steps=[
            "Collect higher-resolution radiometric dating around the boundary.",
            "Compare additional K-Pg biological markers across regions.",
            "Run combined climate and ecosystem simulations with multi-cause stressors.",
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
                description="Sustained rate hikes reduced the value of long-duration bonds.",
                evidence_ids=["svb_ev1", "svb_ev2"],
                posterior_support=0.86,
                uncertainty_contribution=0.10,
            ),
            CausalVariable(
                name="bond_losses",
                description="Held-to-maturity assets created large unrealized losses.",
                evidence_ids=["svb_ev2", "svb_ev3"],
                posterior_support=0.84,
                uncertainty_contribution=0.11,
            ),
            CausalVariable(
                name="deposit_concentration",
                description="Deposits were concentrated in a correlated venture-tech client base.",
                evidence_ids=["svb_ev4"],
                posterior_support=0.80,
                uncertainty_contribution=0.13,
            ),
            CausalVariable(
                name="confidence_shock",
                description="Funding stress and the capital raise triggered a confidence break.",
                evidence_ids=["svb_ev5", "svb_ev6"],
                posterior_support=0.82,
                uncertainty_contribution=0.12,
            ),
            CausalVariable(
                name="bank_run",
                description="Concentrated withdrawals created a fast liquidity crisis.",
                evidence_ids=["svb_ev6", "svb_ev7"],
                posterior_support=0.91,
                uncertainty_contribution=0.08,
            ),
            CausalVariable(
                name="svb_collapse",
                description="SVB lost liquidity rapidly and entered regulatory control.",
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
            name="SVB liquidity spiral hypothesis",
            description="Rate-driven bond losses combined with concentrated deposits and a confidence shock, ending in a bank run and collapse.",
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
                ),
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
                "Connect real bank disclosures and rate-path data sources.",
                "Quantify duration sensitivity versus withdrawal speed.",
                "Compare depositor concentration against peer banks.",
            ],
            is_demo=True,
            demo_topic="svb",
        )

    if topic == "stock":
        variables = [
            CausalVariable(
                name="earnings_miss",
                description="Earnings missed expectations and weakened the company narrative.",
                evidence_ids=["stock_ev1", "stock_ev2"],
                posterior_support=0.84,
                uncertainty_contribution=0.11,
            ),
            CausalVariable(
                name="guidance_cut",
                description="Lower forward guidance deepened bearish expectations.",
                evidence_ids=["stock_ev3"],
                posterior_support=0.79,
                uncertainty_contribution=0.13,
            ),
            CausalVariable(
                name="sector_rotation",
                description="Sector rotation created extra selling pressure on expensive peers.",
                evidence_ids=["stock_ev4"],
                posterior_support=0.72,
                uncertainty_contribution=0.14,
            ),
            CausalVariable(
                name="confidence_breakdown",
                description="Multiple negatives stacked into a rapid confidence breakdown.",
                evidence_ids=["stock_ev5", "stock_ev6"],
                posterior_support=0.83,
                uncertainty_contribution=0.10,
            ),
            CausalVariable(
                name="stock_selloff",
                description="Selling pressure cascaded into a fast stock selloff.",
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
            name="Earnings miss and confidence break hypothesis",
            description="An earnings miss plus weaker guidance damaged confidence, while sector rotation amplified the selloff.",
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
                ),
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
                "Connect real earnings releases and intraday market data.",
                "Separate company-specific damage from sector rotation effects.",
                "Add a timeline distinguishing pre-market and intraday pressure.",
            ],
            is_demo=True,
            demo_topic="stock",
        )

    if topic == "crisis":
        variables = [
            CausalVariable(
                "housing_bubble",
                "The housing bubble built up and then reversed.",
                ["crisis_ev1", "crisis_ev8"],
                0.86,
                0.11,
            ),
            CausalVariable(
                "subprime_lending",
                "Subprime lending expanded default risk among fragile borrowers.",
                ["crisis_ev2"],
                0.82,
                0.12,
            ),
            CausalVariable(
                "toxic_mbs",
                "Securitized assets accumulated hidden housing risk.",
                ["crisis_ev1", "crisis_ev3", "crisis_ev5"],
                0.84,
                0.10,
            ),
            CausalVariable(
                "leverage",
                "High leverage magnified losses when asset prices fell.",
                ["crisis_ev4"],
                0.80,
                0.13,
            ),
            CausalVariable(
                "banking_stress",
                "Financial institutions lost resilience and liquidity buffers.",
                ["crisis_ev3", "crisis_ev4", "crisis_ev6"],
                0.87,
                0.09,
            ),
            CausalVariable(
                "credit_freeze",
                "Credit and interbank markets froze.",
                ["crisis_ev6", "crisis_ev7"],
                0.89,
                0.08,
            ),
            CausalVariable(
                "financial_crisis_2008",
                "The 2008 financial crisis spread across the system.",
                ["crisis_ev7", "crisis_ev8"],
                0.94,
                0.06,
            ),
        ]
        edges = [
            CausalEdge(
                "housing_bubble",
                "toxic_mbs",
                0.83,
                (0.72, 0.91),
                ["crisis_ev1", "crisis_ev8"],
            ),
            CausalEdge(
                "subprime_lending",
                "toxic_mbs",
                0.79,
                (0.66, 0.88),
                ["crisis_ev2", "crisis_ev5"],
            ),
            CausalEdge(
                "toxic_mbs",
                "banking_stress",
                0.85,
                (0.74, 0.92),
                ["crisis_ev3", "crisis_ev5"],
            ),
            CausalEdge("leverage", "banking_stress", 0.81, (0.68, 0.90), ["crisis_ev4"]),
            CausalEdge("banking_stress", "credit_freeze", 0.88, (0.79, 0.94), ["crisis_ev6"]),
            CausalEdge(
                "credit_freeze",
                "financial_crisis_2008",
                0.92,
                (0.84, 0.97),
                ["crisis_ev7"],
            ),
        ]
        hypothesis = HypothesisChain(
            id="demo_crisis_primary",
            name="Housing bubble and leverage failure hypothesis",
            description="A housing reversal, toxic securitization, and leverage combined into banking stress, a credit freeze, and the 2008 crisis.",
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
                    "demo_crisis_primary",
                    "leverage",
                    0.66,
                    0.33,
                    -0.33,
                    True,
                    0.24,
                    0.42,
                    0.69,
                ),
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
                "Connect real house-price, default, and funding-market time series.",
                "Compare leverage effects against securitization structure effects.",
                "Add regulatory and liquidity-event timeline detail.",
            ],
            is_demo=True,
            demo_topic="crisis",
        )

    if topic == "rent":
        variables = [
            CausalVariable(
                "zoning_constraints",
                "Zoning and permitting rules constrained new supply.",
                ["rent_ev2"],
                0.78,
                0.13,
            ),
            CausalVariable(
                "investor_pressure",
                "Investor ownership and short-term rentals displaced long-term supply.",
                ["rent_ev4"],
                0.70,
                0.15,
            ),
            CausalVariable(
                "housing_supply_shortage",
                "Housing supply remained structurally short.",
                ["rent_ev1", "rent_ev2", "rent_ev4"],
                0.87,
                0.09,
            ),
            CausalVariable(
                "income_demand",
                "Income concentration increased willingness to pay in core areas.",
                ["rent_ev3", "rent_ev7"],
                0.81,
                0.11,
            ),
            CausalVariable(
                "construction_costs",
                "Development and holding costs climbed.",
                ["rent_ev5"],
                0.72,
                0.14,
            ),
            CausalVariable(
                "rent_pressure",
                "Supply shortages and cost pressures pushed rents upward.",
                ["rent_ev1", "rent_ev3", "rent_ev5", "rent_ev6"],
                0.88,
                0.08,
            ),
            CausalVariable(
                "high_rent",
                "Rent stayed elevated for a long period.",
                ["rent_ev6", "rent_ev7", "rent_ev8"],
                0.93,
                0.06,
            ),
        ]
        edges = [
            CausalEdge(
                "zoning_constraints",
                "housing_supply_shortage",
                0.82,
                (0.69, 0.90),
                ["rent_ev2"],
            ),
            CausalEdge(
                "investor_pressure",
                "housing_supply_shortage",
                0.66,
                (0.52, 0.79),
                ["rent_ev4"],
            ),
            CausalEdge(
                "housing_supply_shortage",
                "rent_pressure",
                0.89,
                (0.80, 0.95),
                ["rent_ev1", "rent_ev6"],
            ),
            CausalEdge(
                "income_demand",
                "rent_pressure",
                0.77,
                (0.64, 0.87),
                ["rent_ev3", "rent_ev7"],
            ),
            CausalEdge(
                "construction_costs",
                "rent_pressure",
                0.63,
                (0.49, 0.76),
                ["rent_ev5"],
            ),
            CausalEdge(
                "rent_pressure",
                "high_rent",
                0.93,
                (0.85, 0.97),
                ["rent_ev6", "rent_ev8"],
            ),
        ]
        hypothesis = HypothesisChain(
            id="demo_rent_primary",
            name="Supply constraint and demand concentration hypothesis",
            description="Constrained supply, concentrated demand, and higher costs worked together to keep rents high.",
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
                ),
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
                "Connect city-level rent and housing-supply time series.",
                "Estimate marginal contribution of zoning versus costs.",
                "Add migration and employment concentration detail.",
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
    "ofoxai": {
        "label": "OfoxAI\uff08OpenAI-compatible\uff09",
        "base_url": "https://api.ofox.ai/v1",
        "models": {
            "openai/gpt-5.4-mini": {
                "label": "GPT-5.4 Mini\uff08OfoxAI\uff0c\u9ed8\u8ba4\uff09",
                "json_mode": True,
            },
            "openai/gpt-5.4": {"label": "GPT-5.4\uff08OfoxAI\uff09", "json_mode": True},
        },
    },
    "openai": {
        "label": "OpenAI（直连）",
        "base_url": None,
        "models": {
            "gpt-4o-mini": {"label": "GPT-4o Mini（直连）", "json_mode": True},
            "gpt-4o": {"label": "GPT-4o（直连）", "json_mode": True},
            "gpt-4.1-mini": {"label": "GPT-4.1 Mini（直连）", "json_mode": True},
            "gpt-4.1": {"label": "GPT-4.1（直连）", "json_mode": True},
        },
    },
    "dashscope": {
        "label": "DashScope / 阿里百炼（官方）",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": {
            "qwen3-max": {"label": "Qwen3 Max（旗舰）", "json_mode": True},
            "qwen3.6-plus": {"label": "Qwen3.6 Plus（推荐）", "json_mode": True},
            "qwen3.5-plus": {"label": "Qwen3.5 Plus", "json_mode": True},
            "qwen3.5-flash": {"label": "Qwen3.5 Flash（快速）", "json_mode": True},
            "qwen-max": {"label": "Qwen Max（经典）", "json_mode": True},
            "qwen-plus": {"label": "Qwen Plus", "json_mode": True},
            "qwen-turbo": {"label": "Qwen Turbo（极速）", "json_mode": True},
            "qwen-flash": {"label": "Qwen Flash（快速低价）", "json_mode": True},
            "qwen-long": {"label": "Qwen Long（1M 上下文）", "json_mode": True},
            "qwq-32b-preview": {"label": "QwQ 32B（推理）", "json_mode": True},
            "qwen-coder-plus": {"label": "Qwen Coder Plus", "json_mode": True},
        },
    },
    "zhipu": {
        "label": "Zhipu / 智谱（官方）",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "models": {
            "glm-5.1": {"label": "GLM-5.1（最新旗舰）", "json_mode": True},
            "glm-5": {"label": "GLM-5", "json_mode": True},
            "glm-5-turbo": {"label": "GLM-5 Turbo", "json_mode": True},
            "glm-4.7": {"label": "GLM-4.7", "json_mode": True},
            "glm-4.7-flashx": {"label": "GLM-4.7 FlashX（快速）", "json_mode": True},
            "glm-4.7-flash": {"label": "GLM-4.7 Flash（免费）", "json_mode": True},
            "glm-4.6": {"label": "GLM-4.6", "json_mode": True},
            "glm-4-plus": {"label": "GLM-4 Plus（推荐）", "json_mode": True},
            "glm-4.5-air": {"label": "GLM-4.5 Air（性价比）", "json_mode": True},
            "glm-4.5-airx": {"label": "GLM-4.5 AirX（极速）", "json_mode": True},
            "glm-4-air-250414": {"label": "GLM-4 Air", "json_mode": True},
            "glm-4-airx": {"label": "GLM-4 AirX（极速）", "json_mode": True},
            "glm-4-long": {"label": "GLM-4 Long（1M 上下文）", "json_mode": True},
            "glm-4-flash-250414": {"label": "GLM-4 Flash（免费）", "json_mode": True},
        },
    },
    "moonshot": {
        "label": "Moonshot / Kimi（官方）",
        "base_url": "https://api.moonshot.cn/v1",
        "models": {
            "kimi-k2.5": {"label": "Kimi K2.5（最新旗舰）", "json_mode": True},
            "kimi-k2-turbo-preview": {"label": "Kimi K2 Turbo（推荐）", "json_mode": True},
            "kimi-k2-0905-preview": {"label": "Kimi K2 (0905)", "json_mode": True},
            "kimi-k2-thinking": {"label": "Kimi K2 Thinking（推理）", "json_mode": True},
            "kimi-k2-thinking-turbo": {"label": "Kimi K2 Thinking Turbo", "json_mode": True},
            "moonshot-v1-8k": {"label": "Moonshot V1 8K", "json_mode": True},
            "moonshot-v1-32k": {"label": "Moonshot V1 32K", "json_mode": True},
            "moonshot-v1-128k": {"label": "Moonshot V1 128K", "json_mode": True},
        },
    },
    "deepseek": {
        "label": "DeepSeek（官方）",
        "base_url": "https://api.deepseek.com/v1",
        "models": {
            "deepseek-chat": {"label": "DeepSeek Chat V3.2（推荐）", "json_mode": True},
            "deepseek-reasoner": {"label": "DeepSeek Reasoner V3.2（推理）", "json_mode": True},
        },
    },
}

def _select_source_names(configured_sources: str | None, domain: str) -> list[str]:
    from retrocause.evidence_access import QueryPlan, broker_source_names

    plan = QueryPlan(
        query="",
        domain=domain,
        time_range=None,
        language="en",
        entities=[],
        scenario="policy" if domain == "geopolitics" else "market"
        if domain in {"finance", "business"}
        else "academic",
    )
    return broker_source_names(configured_sources, plan)


def _available_source_factories() -> dict[str, Callable[[], object]]:
    from retrocause.sources.ap_news import APNewsAdapter as _AP
    from retrocause.sources.arxiv import ArxivSourceAdapter as _Arxiv
    from retrocause.sources.federal_register import FederalRegisterAdapter as _FederalRegister
    from retrocause.sources.gdelt import GdeltNewsAdapter as _Gdelt
    from retrocause.sources.semantic_scholar import SemanticScholarAdapter as _SS
    from retrocause.sources.web import WebSearchAdapter as _Web

    available_sources: dict[str, Callable[[], object]] = {
        "ap_news": _AP,
        "arxiv": _Arxiv,
        "federal_register": _FederalRegister,
        "semantic_scholar": _SS,
        "web": _Web,
        "gdelt": _Gdelt,
    }
    return available_sources


def _available_source_classes_from_env() -> dict[str, type]:
    from retrocause.sources.ap_news import APNewsAdapter as _AP
    from retrocause.sources.arxiv import ArxivSourceAdapter as _Arxiv
    from retrocause.sources.federal_register import FederalRegisterAdapter as _FederalRegister
    from retrocause.sources.gdelt import GdeltNewsAdapter as _Gdelt
    from retrocause.sources.semantic_scholar import SemanticScholarAdapter as _SS
    from retrocause.sources.web import WebSearchAdapter as _Web

    available_sources: dict[str, type] = {
        "ap_news": _AP,
        "arxiv": _Arxiv,
        "federal_register": _FederalRegister,
        "semantic_scholar": _SS,
        "web": _Web,
        "gdelt": _Gdelt,
    }
    return available_sources
