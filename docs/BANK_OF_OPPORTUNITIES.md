# Bank of Opportunities - Feature Design

## Concept

The **Bank of Opportunities** is a persistent collection where users can save promising opportunities discovered during conversations. Each banked opportunity preserves its full context - the problem it addresses, the analysis that surfaced it, the frameworks applied, and the conversation thread that led to its discovery.

Think of it as a "strategic idea vault" - users can return to any banked opportunity and immediately deep dive with Larry, picking up exactly where they left off, but now with fresh eyes or new information.

---

## User Experience Flow

### Act 1: Discovery (During Conversation)

```
┌────────────────────────────────────────────────────────────────┐
│  Conversation with Larry                                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Larry: "Based on our CSIO analysis, I see 3 promising        │
│          cross-sectional opportunities..."                     │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  🎯 Opportunity Card                                     │  │
│  │  ─────────────────────────────────────────────────────  │  │
│  │  "AI-Powered Async Standup Platform"                    │  │
│  │                                                          │  │
│  │  CSIO Score: 7.2/10                                     │  │
│  │  Cross-Section: Remote Work × AI Summarization          │  │
│  │                                                          │  │
│  │  [Explore] [Compare]  [🏦 Bank It]                      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**User Action**: Clicks "🏦 Bank It"

### Act 2: Banking (Context Capture)

```
┌────────────────────────────────────────────────────────────────┐
│  💾 Save to Opportunity Bank                                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Opportunity: "AI-Powered Async Standup Platform"              │
│                                                                │
│  ┌─ Context Being Saved ─────────────────────────────────┐    │
│  │                                                        │    │
│  │  📋 Problem Context                                    │    │
│  │     "Reducing meeting fatigue for distributed teams"   │    │
│  │                                                        │    │
│  │  🔬 Analyses Applied                                   │    │
│  │     ✓ Minto Pyramid (SCQA)                            │    │
│  │     ✓ CSIO Cross-Section                              │    │
│  │     ✓ Beautiful Question                              │    │
│  │                                                        │    │
│  │  💡 Key Insights                                       │    │
│  │     • 73% of standups could be async                  │    │
│  │     • AI can summarize 15-min video to 2-min digest   │    │
│  │     • Market gap: no tool owns "async team sync"      │    │
│  │                                                        │    │
│  │  📝 Your Notes (optional)                             │    │
│  │  ┌────────────────────────────────────────────────┐   │    │
│  │  │ Validate with 3 engineering managers first...  │   │    │
│  │  └────────────────────────────────────────────────┘   │    │
│  │                                                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                │
│  Tags: [remote-work] [AI] [productivity] [+add tag]            │
│                                                                │
│  Priority: ○ Low  ● Medium  ○ High  ○ Critical                 │
│                                                                │
│              [Cancel]  [🏦 Save to Bank]                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Act 3: The Bank (Dashboard View)

```
┌────────────────────────────────────────────────────────────────┐
│  🏦 Opportunity Bank                          [+ New Problem]  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Filter: [All] [High Priority] [By Problem] [By Tag]           │
│  Sort:   [Recent] [CSIO Score] [Priority]                      │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 🎯 AI-Powered Async Standup Platform                    │  │
│  │    ────────────────────────────────────────────────────  │  │
│  │    Problem: Meeting fatigue for distributed teams       │  │
│  │    Score: 7.2  │  Priority: ●● Medium  │  Banked: 2d ago│  │
│  │    Tags: remote-work, AI, productivity                  │  │
│  │                                                          │  │
│  │    [🔍 Deep Dive]  [📊 Compare]  [📤 Export]  [...]     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 🎯 Gamified Therapy for Anxiety                         │  │
│  │    ────────────────────────────────────────────────────  │  │
│  │    Problem: Mental health access for Gen Z              │  │
│  │    Score: 8.1  │  Priority: ●●● High  │  Banked: 1w ago │  │
│  │    Tags: healthcare, gaming, mental-health              │  │
│  │                                                          │  │
│  │    [🔍 Deep Dive]  [📊 Compare]  [📤 Export]  [...]     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 🎯 Smart Contract Legal Templates                       │  │
│  │    ────────────────────────────────────────────────────  │  │
│  │    Problem: Legal complexity for startups               │  │
│  │    Score: 6.5  │  Priority: ● Low     │  Banked: 2w ago │  │
│  │    Tags: legal, blockchain, automation                  │  │
│  │                                                          │  │
│  │    [🔍 Deep Dive]  [📊 Compare]  [📤 Export]  [...]     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Act 4: Deep Dive (Context Restoration)

When user clicks "🔍 Deep Dive":

```
┌────────────────────────────────────────────────────────────────┐
│  🔍 Deep Dive: AI-Powered Async Standup Platform               │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─ Context Restored ────────────────────────────────────┐    │
│  │ Larry has access to:                                   │    │
│  │ • Original problem: "Meeting fatigue for distributed   │    │
│  │   teams"                                               │    │
│  │ • 3 framework analyses (Minto, CSIO, Beautiful Q)     │    │
│  │ • 7 key insights from original conversation           │    │
│  │ • Your note: "Validate with 3 engineering managers"   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                │
│  What would you like to explore?                               │
│                                                                │
│  [Validate Assumptions]  [Market Research]  [Build MVP Plan]   │
│  [Compare Alternatives]  [Find Competitors]  [Custom...]       │
│                                                                │
│  ─────────────────────────────────────────────────────────────│
│                                                                │
│  Larry: "Welcome back! Last time we identified async          │
│          standups as a promising opportunity with a 7.2       │
│          CSIO score. You wanted to validate with engineering  │
│          managers first. Should we design a validation        │
│          approach?"                                            │
│                                                                │
│  You: [                                                    ]   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Neo4j Schema Design

### Core Nodes

```cypher
// BankedOpportunity - The main entity in the Bank
CREATE (bo:BankedOpportunity {
  id: "bo_uuid",
  name: "AI-Powered Async Standup Platform",
  description: "Video standup platform that uses AI to summarize...",
  csio_score: 7.2,
  priority: "MEDIUM",  // LOW, MEDIUM, HIGH, CRITICAL
  status: "ACTIVE",    // ACTIVE, ARCHIVED, VALIDATED, REJECTED
  user_notes: "Validate with 3 engineering managers first",
  banked_at: datetime(),
  last_accessed: datetime(),
  deep_dive_count: 0
})

// OpportunityContext - Preserves the full context
CREATE (ctx:OpportunityContext {
  id: "ctx_uuid",
  problem_statement: "Reducing meeting fatigue for distributed teams",
  problem_clarity_score: 0.85,
  problem_what: "Daily standups consume too much time",
  problem_who: "Distributed engineering teams",
  problem_success: "Teams feel aligned without synchronous meetings",
  conversation_summary: "User explored async communication...",
  key_insights: ["73% of standups could be async", "AI can summarize..."],
  created_at: datetime()
})

// FrameworkAnalysis - Each framework applied
CREATE (fa:FrameworkAnalysis {
  id: "fa_uuid",
  framework_type: "CSIO",  // MINTO, CSIO, BEAUTIFUL_QUESTION, DOMAIN_ANALYSIS, etc.
  framework_output: "## Cross-Section Analysis...",
  key_findings: ["Cross-section: Remote Work × AI", "Score: 7.2"],
  created_at: datetime()
})

// DeepDiveSession - Track each return visit
CREATE (dds:DeepDiveSession {
  id: "dds_uuid",
  started_at: datetime(),
  ended_at: datetime(),
  focus: "Market Research",
  new_insights: ["Found 3 competitors", "Gap in async-first tools"],
  outcome: "Decided to proceed with validation"
})
```

### Relationships

```cypher
// User owns banked opportunities
(u:User)-[:OWNS]->(bo:BankedOpportunity)

// Opportunity has context
(bo:BankedOpportunity)-[:HAS_CONTEXT]->(ctx:OpportunityContext)

// Context came from a problem
(ctx:OpportunityContext)-[:ORIGINATED_FROM]->(p:Problem)

// Context includes framework analyses
(ctx:OpportunityContext)-[:INCLUDES_ANALYSIS]->(fa:FrameworkAnalysis)

// Framework analysis used a specific framework
(fa:FrameworkAnalysis)-[:USED_FRAMEWORK]->(f:Framework)

// Opportunity linked to original conversation
(bo:BankedOpportunity)-[:DISCOVERED_IN]->(s:Session)

// Deep dive sessions
(bo:BankedOpportunity)-[:HAS_DEEP_DIVE]->(dds:DeepDiveSession)
(dds:DeepDiveSession)-[:SPAWNED_SESSION]->(s:Session)

// Cross-reference with InnovationOpportunity (existing)
(bo:BankedOpportunity)-[:REFERENCES]->(io:InnovationOpportunity)

// Tags for filtering
(bo:BankedOpportunity)-[:TAGGED_WITH]->(t:Tag)

// Opportunity addresses a domain intersection
(bo:BankedOpportunity)-[:INTERSECTS]->(d1:Domain)
(bo:BankedOpportunity)-[:INTERSECTS]->(d2:Domain)
```

### Full Schema Visualization

```
                                    ┌─────────────┐
                                    │    User     │
                                    └──────┬──────┘
                                           │ OWNS
                                           ▼
┌──────────────┐  DISCOVERED_IN   ┌──────────────────┐  HAS_CONTEXT   ┌───────────────────┐
│   Session    │◄─────────────────│ BankedOpportunity │──────────────►│ OpportunityContext │
└──────────────┘                  └────────┬─────────┘               └─────────┬─────────┘
       ▲                                   │                                   │
       │                                   │ HAS_DEEP_DIVE                     │ ORIGINATED_FROM
       │ SPAWNED_SESSION                   ▼                                   ▼
┌──────┴─────────┐                ┌────────────────┐               ┌───────────────────┐
│ DeepDiveSession │◄──────────────│ DeepDiveSession │               │     Problem       │
└────────────────┘                └────────────────┘               └───────────────────┘
                                           │
                                           │ INCLUDES_ANALYSIS
                                           ▼
                              ┌─────────────────────┐  USED_FRAMEWORK  ┌───────────┐
                              │  FrameworkAnalysis  │─────────────────►│ Framework │
                              └─────────────────────┘                  └───────────┘

Additional Relationships:
- BankedOpportunity -[:TAGGED_WITH]-> Tag
- BankedOpportunity -[:INTERSECTS]-> Domain
- BankedOpportunity -[:REFERENCES]-> InnovationOpportunity (existing PWS entities)
```

---

## API Endpoints

### Bank an Opportunity

```python
POST /api/opportunities/bank
{
  "opportunity": {
    "name": "AI-Powered Async Standup Platform",
    "description": "...",
    "csio_score": 7.2
  },
  "context": {
    "session_id": "sess_abc123",
    "problem_id": "prob_xyz789",
    "framework_analyses": ["fa_minto_001", "fa_csio_002", "fa_bq_003"]
  },
  "user_input": {
    "notes": "Validate with 3 engineering managers first",
    "priority": "MEDIUM",
    "tags": ["remote-work", "AI", "productivity"]
  }
}
```

### List Banked Opportunities

```python
GET /api/opportunities/bank?
    user_id=user_001&
    priority=HIGH,MEDIUM&
    tags=AI&
    sort=csio_score&
    order=desc
```

### Deep Dive into Opportunity

```python
POST /api/opportunities/{opportunity_id}/deep-dive
{
  "focus": "Market Research",  // or "Validate Assumptions", "Build MVP Plan", etc.
  "additional_context": "I spoke with 2 engineering managers who confirmed the pain point"
}

Response:
{
  "session_id": "sess_new_123",
  "restored_context": {
    "problem": {...},
    "analyses": [...],
    "insights": [...],
    "user_notes": "..."
  },
  "larry_opening": "Welcome back! Last time we identified..."
}
```

---

## Cypher Queries

### Bank a New Opportunity

```cypher
// Create the banked opportunity with full context
CREATE (bo:BankedOpportunity {
  id: $opportunity_id,
  name: $name,
  description: $description,
  csio_score: $csio_score,
  priority: $priority,
  status: 'ACTIVE',
  user_notes: $notes,
  banked_at: datetime(),
  last_accessed: datetime(),
  deep_dive_count: 0
})

// Link to user
WITH bo
MATCH (u:User {id: $user_id})
CREATE (u)-[:OWNS]->(bo)

// Create and link context
WITH bo
CREATE (ctx:OpportunityContext {
  id: randomUUID(),
  problem_statement: $problem_statement,
  problem_clarity_score: $clarity_score,
  problem_what: $what,
  problem_who: $who,
  problem_success: $success,
  conversation_summary: $summary,
  key_insights: $insights,
  created_at: datetime()
})
CREATE (bo)-[:HAS_CONTEXT]->(ctx)

// Link to original session
WITH bo
MATCH (s:Session {id: $session_id})
CREATE (bo)-[:DISCOVERED_IN]->(s)

// Link to original problem
WITH bo, ctx
MATCH (p:Problem {id: $problem_id})
CREATE (ctx)-[:ORIGINATED_FROM]->(p)

// Link framework analyses
WITH bo, ctx
UNWIND $framework_analysis_ids AS fa_id
MATCH (fa:FrameworkAnalysis {id: fa_id})
CREATE (ctx)-[:INCLUDES_ANALYSIS]->(fa)

// Add tags
WITH bo
UNWIND $tags AS tag_name
MERGE (t:Tag {name: tag_name})
CREATE (bo)-[:TAGGED_WITH]->(t)

RETURN bo
```

### List User's Banked Opportunities

```cypher
MATCH (u:User {id: $user_id})-[:OWNS]->(bo:BankedOpportunity)
WHERE bo.status = 'ACTIVE'
AND ($priority IS NULL OR bo.priority IN $priority)

OPTIONAL MATCH (bo)-[:TAGGED_WITH]->(t:Tag)
WHERE $tags IS NULL OR t.name IN $tags

OPTIONAL MATCH (bo)-[:HAS_CONTEXT]->(ctx:OpportunityContext)

RETURN bo {
  .*,
  tags: collect(DISTINCT t.name),
  problem_statement: ctx.problem_statement,
  key_insights: ctx.key_insights
}
ORDER BY
  CASE WHEN $sort = 'csio_score' THEN bo.csio_score END DESC,
  CASE WHEN $sort = 'priority' THEN
    CASE bo.priority
      WHEN 'CRITICAL' THEN 1
      WHEN 'HIGH' THEN 2
      WHEN 'MEDIUM' THEN 3
      ELSE 4
    END
  END ASC,
  CASE WHEN $sort = 'recent' OR $sort IS NULL THEN bo.banked_at END DESC
LIMIT $limit
```

### Restore Context for Deep Dive

```cypher
// Get full context for deep dive
MATCH (bo:BankedOpportunity {id: $opportunity_id})
MATCH (bo)-[:HAS_CONTEXT]->(ctx:OpportunityContext)

// Get original problem
OPTIONAL MATCH (ctx)-[:ORIGINATED_FROM]->(p:Problem)

// Get all framework analyses
OPTIONAL MATCH (ctx)-[:INCLUDES_ANALYSIS]->(fa:FrameworkAnalysis)
OPTIONAL MATCH (fa)-[:USED_FRAMEWORK]->(f:Framework)

// Get original session for conversation history
OPTIONAL MATCH (bo)-[:DISCOVERED_IN]->(orig_session:Session)

// Get previous deep dives
OPTIONAL MATCH (bo)-[:HAS_DEEP_DIVE]->(prev_dd:DeepDiveSession)

// Update access tracking
SET bo.last_accessed = datetime(),
    bo.deep_dive_count = bo.deep_dive_count + 1

RETURN {
  opportunity: bo {.*},
  context: ctx {.*},
  problem: p {.*},
  analyses: collect(DISTINCT {
    framework: f.name,
    type: fa.framework_type,
    output: fa.framework_output,
    findings: fa.key_findings
  }),
  original_session_id: orig_session.id,
  previous_deep_dives: collect(DISTINCT prev_dd {.*})
}
```

### Record Deep Dive Session

```cypher
// Create deep dive session
MATCH (bo:BankedOpportunity {id: $opportunity_id})
CREATE (dds:DeepDiveSession {
  id: randomUUID(),
  started_at: datetime(),
  focus: $focus,
  initial_context: $additional_context
})
CREATE (bo)-[:HAS_DEEP_DIVE]->(dds)

// Create new conversation session
CREATE (s:Session {
  id: randomUUID(),
  type: 'DEEP_DIVE',
  started_at: datetime()
})
CREATE (dds)-[:SPAWNED_SESSION]->(s)

RETURN dds, s
```

---

## Integration with Mindrian Agents

### Larry's Context Awareness

When starting a deep dive, Larry receives:

```python
@dataclass
class DeepDiveContext:
    """Context restored for Larry when user deep dives into banked opportunity"""

    # The opportunity itself
    opportunity_name: str
    opportunity_description: str
    csio_score: float

    # Original problem context
    problem_what: str
    problem_who: str
    problem_success: str
    problem_clarity_score: float

    # Previous analyses (summaries)
    minto_summary: Optional[str]
    csio_summary: Optional[str]
    beautiful_question: Optional[str]
    domain_analysis: Optional[str]

    # User's notes and history
    user_notes: str
    previous_deep_dives: List[Dict]  # [{focus, insights, outcome}]

    # Conversation context
    key_insights: List[str]
    conversation_summary: str

    def to_larry_prompt(self) -> str:
        """Generate context prompt for Larry"""
        return f"""
## Restored Context: Deep Dive Session

### Opportunity
**{self.opportunity_name}** (CSIO Score: {self.csio_score})
{self.opportunity_description}

### Original Problem
- **What:** {self.problem_what}
- **Who:** {self.problem_who}
- **Success:** {self.problem_success}
- **Clarity:** {self.problem_clarity_score:.0%}

### Previous Analyses
{self._format_analyses()}

### Key Insights from Original Exploration
{self._format_insights()}

### User Notes
{self.user_notes}

### Previous Deep Dives
{self._format_previous_deep_dives()}

---

The user is returning to explore this opportunity further.
Acknowledge the context and ask what aspect they'd like to explore.
"""
```

### Team Orchestration for Deep Dive

```python
# teams/deep_dive_team.py

class DeepDiveTeam:
    """Team configured for deep diving into banked opportunities"""

    def __init__(self):
        # Larry leads with restored context
        self.larry = LarryAgent(context_aware=True)

        # Framework agents available on-demand
        self.minto = MintoPyramidAgent()
        self.csio = CSIOAgent()
        self.pws = PWSValidationAgent()
        self.devil = DevilsAdvocateAgent()

        # Research for validation
        self.tavily = TavilyResearchAgent()

    async def start_deep_dive(
        self,
        opportunity_id: str,
        focus: str,
        user_context: str = ""
    ) -> DeepDiveSession:
        """Start a deep dive session with full context restoration"""

        # 1. Restore context from Neo4j
        context = await self._restore_context(opportunity_id)

        # 2. Record the deep dive session
        session = await self._create_session(opportunity_id, focus)

        # 3. Configure Larry with restored context
        larry_context = context.to_larry_prompt()

        # 4. Add focus-specific instructions
        focus_instructions = self._get_focus_instructions(focus)

        # 5. Start conversation
        opening = await self.larry.start_with_context(
            context=larry_context,
            focus=focus_instructions,
            user_addition=user_context
        )

        return DeepDiveSession(
            session_id=session.id,
            opening_message=opening,
            available_actions=self._get_available_actions(focus)
        )
```

---

## Mobile UX: Drag to Bank

For touch interfaces, the banking action is a gesture:

```
┌──────────────────────────────┐
│                              │
│  ┌────────────────────────┐  │
│  │ 🎯 Opportunity Card    │  │
│  │                        │  │
│  │ "AI Async Standups"    │  │
│  │ Score: 7.2             │  │
│  │                        │  │
│  └────────────────────────┘  │
│           │                  │
│           │ ← User drags     │
│           │   down           │
│           ▼                  │
│  ┌────────────────────────┐  │
│  │ 🏦 Drop to Bank        │  │
│  │    ──────────────────  │  │
│  │    Release to save     │  │
│  │    with full context   │  │
│  └────────────────────────┘  │
│                              │
└──────────────────────────────┘
```

---

## Success Metrics

1. **Banking Rate**: % of discovered opportunities that get banked
2. **Return Rate**: % of banked opportunities that get deep-dived
3. **Context Utility**: User rating of "was the restored context helpful?"
4. **Conversion Rate**: % of banked opportunities that lead to action (validation, MVP, etc.)
5. **Time to Value**: Average time from banking to meaningful outcome

---

---

## Process Integration: How It Fits Into the Workflow

### The Complete Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MINDRIAN CONVERSATION FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │  User Challenge │
                              └────────┬────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │         DeepResearchTeam              │
                    │  ┌──────────────────────────────┐    │
                    │  │ Larry → Minto → Beautiful Q  │    │
                    │  │ → Domain → CSIO → Synthesis  │    │
                    │  └──────────────────────────────┘    │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │     Breakthrough Opportunities        │
                    │   ┌────────┐ ┌────────┐ ┌────────┐   │
                    │   │ Opp 1  │ │ Opp 2  │ │ Opp 3  │   │
                    │   │ 7.2/10 │ │ 8.1/10 │ │ 6.5/10 │   │
                    │   └───┬────┘ └───┬────┘ └───┬────┘   │
                    └───────┼──────────┼──────────┼────────┘
                            │          │          │
                    User clicks "🏦 Bank It"      │
                            │          │          │
                            ▼          ▼          ▼
                    ┌──────────────────────────────────────┐
                    │      OpportunityBankService           │
                    │  ┌────────────────────────────────┐  │
                    │  │ • Captures full context        │  │
                    │  │ • Stores to Neo4j              │  │
                    │  │ • Links all analyses           │  │
                    │  │ • Preserves problem clarity    │  │
                    │  └────────────────────────────────┘  │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │         🏦 Opportunity Bank           │
                    │   [Filter] [Sort] [Search]           │
                    │   ┌────────────────────────────────┐ │
                    │   │ Banked opportunities with      │ │
                    │   │ full context preserved         │ │
                    │   └────────────────────────────────┘ │
                    └──────────────────┬───────────────────┘
                                       │
                         User clicks "🔍 Deep Dive"
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │          DeepDiveTeam                 │
                    │  ┌────────────────────────────────┐  │
                    │  │ 1. Restore context             │  │
                    │  │ 2. Configure Larry + focus     │  │
                    │  │ 3. Bring in research/devil     │  │
                    │  │ 4. Record new insights         │  │
                    │  └────────────────────────────────┘  │
                    └──────────────────────────────────────┘
```

### Key Integration Points

#### 1. Banking from DeepResearchResult

```python
# In the UI/API after DeepResearchTeam completes
from mindrian.services.opportunity_bank import OpportunityBankService

bank = OpportunityBankService()

# User clicks "Bank It" on an opportunity from the report
opportunity = await bank.bank_from_research_result(
    research_result=deep_research_result,
    opportunity_name="AI Async Standups",
    opportunity_description="Video standup platform with AI summarization",
    csio_score=7.2,
    user_id=current_user.id,
    cross_section_type="Industry × Technology",
    cross_section_elements=["Remote Work", "AI Summarization"],
    priority=OpportunityPriority.MEDIUM,
    tags=["remote-work", "AI", "productivity"],
    user_notes="Validate with engineering managers first",
    session_id=current_session.id,
)
```

#### 2. Deep Dive from Bank

```python
from mindrian.teams.deep_dive_team import DeepDiveTeam, DeepDiveFocus

dive_team = DeepDiveTeam()

# User selects opportunity and focus
result = await dive_team.dive(
    opportunity_id="opp_abc123",
    focus=DeepDiveFocus.VALIDATE_ASSUMPTIONS,
    user_id=current_user.id,
)

# Display Larry's opening with restored context
print(result.conversation_output)
# "Welcome back! I remember we identified AI Async Standups as promising
#  because it scores 7.2 on CSIO with strong timing indicators.
#  You wanted to validate with engineering managers - let's design
#  that validation. What assumptions are you most uncertain about?"

# Continue the conversation
response = await dive_team.continue_dive(
    session_id=result.session_id,
    user_message="The main assumption is that teams want async standups",
    request_devil=True,  # Bring in Devil's Advocate
)

print(response["larry"])   # Larry's response
print(response["devil"])   # Devil's challenge to the assumption
```

#### 3. Recording Insights Back

```python
# When user completes the deep dive
await dive_team.complete_dive(
    session_id=result.session_id,
    insights=[
        "3/3 engineering managers confirmed async standup pain",
        "Current tools (Slack, Loom) are workarounds, not solutions",
        "Willing to pay $5-10/user/month",
    ],
    outcome="Assumptions validated - proceed to MVP planning",
    next_focus=DeepDiveFocus.BUILD_MVP_PLAN,
)

# Opportunity now has updated insights in Neo4j
```

---

## File Structure

```
mindrian-agno/
├── mindrian/
│   ├── services/
│   │   ├── __init__.py
│   │   └── opportunity_bank.py      # OpportunityBankService
│   │
│   ├── teams/
│   │   ├── deep_research_team.py    # Initial exploration
│   │   └── deep_dive_team.py        # Return to banked opportunities
│   │
│   └── handoff/
│       └── context.py               # Context structures used for banking
│
└── docs/
    └── BANK_OF_OPPORTUNITIES.md     # This document
```

---

## Implementation Priority

### Phase 1: Core Banking (Week 1) ✅
- [x] Neo4j schema for BankedOpportunity and OpportunityContext
- [x] OpportunityBankService with bank/list/get operations
- [ ] API endpoints for banking and listing
- [ ] Basic UI for banking from conversation

### Phase 2: Context Restoration (Week 2) ✅
- [x] Deep dive session creation
- [x] Larry context restoration
- [x] DeepDiveTeam with focus areas
- [x] Framework analysis linking

### Phase 3: Rich UX (Week 3)
- [ ] Bank dashboard with filtering/sorting
- [ ] Tags and priority management
- [ ] Mobile drag-to-bank gesture

### Phase 4: Intelligence (Week 4)
- [ ] Opportunity comparison view
- [ ] Cross-opportunity insights
- [ ] Automated opportunity scoring updates
- [ ] Smart focus suggestions based on opportunity state
