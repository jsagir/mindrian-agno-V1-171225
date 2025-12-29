"""
Chat Routes v4 - Action-Oriented Larry with Role Switching

KEY CHANGES:
1. 5-question limit before transitioning to value mode
2. PWS Brain RAG for grounded responses
3. Role switching (Larry → Coach → Expert → Devil)
4. Frustration detection and response adjustment
"""

import os
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import anthropic

# Direct imports to avoid mindrian.__init__ which requires agno
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import prompts directly from file
from mindrian.prompts.larry_system_prompt_v4 import (
    LARRY_SYSTEM_PROMPT_V4,
    LARRY_COMPACT_PROMPT_V4,
)

# Import PWS Brain directly
try:
    from mindrian.tools.pinecone_pws_brain import PineconePWSBrain, get_pws_brain
except ImportError:
    # Fallback if pinecone not available
    PineconePWSBrain = None
    def get_pws_brain():
        return None

router = APIRouter()

# Claude client
client = anthropic.Anthropic()

# Session storage
sessions: Dict[str, Dict[str, Any]] = {}

# PWS Brain for RAG
pws_brain = get_pws_brain()


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class RoleSuggestion(BaseModel):
    """A suggested role button for the UI."""
    role_id: str
    name: str
    title: str
    reason: str  # Why this role is suggested now


class RoleInfo(BaseModel):
    """Full role information for UI display."""
    role_id: str
    name: str
    title: str
    description: str
    icon: str  # Emoji icon for the role
    is_current: bool  # Whether this is the active role


class ChatResponse(BaseModel):
    session_id: str
    response: str
    current_role: str
    question_count: int
    problem_clarity: Dict[str, Any]
    suggested_actions: Optional[List[str]] = None
    suggested_roles: Optional[List[RoleSuggestion]] = None  # Context-aware suggestions
    available_roles: Optional[List[RoleInfo]] = None  # ALL roles for UI buttons


# =============================================================================
# Role Definitions
# =============================================================================

ROLES = {
    "larry": {
        "name": "Larry",
        "title": "The Clarifier",
        "description": "Asks questions to understand the problem (max 5)",
        "icon": "🔍",
        "system_prompt": LARRY_SYSTEM_PROMPT_V4,
    },
    "coach": {
        "name": "Coach",
        "title": "The Guide",
        "description": "Walks through frameworks step-by-step",
        "icon": "🧭",
        "system_prompt": """You are now in COACH mode. Your job is to guide the user through a structured thinking process.

Based on the conversation so far, apply the most relevant PWS framework:
- For unclear customer needs: JTBD (Jobs to Be Done)
- For messy thinking: Minto Pyramid (SCQA)
- For future uncertainty: Scenario Analysis
- For idea validation: PWS 4-Pillar Scorecard

Walk them through step by step. Be patient. Check understanding.
Give CONCRETE GUIDANCE, not just questions.

Format each step clearly:
"Step 1: [action]
Here's what this means for you: [application]
Try this: [specific task]"
""",
    },
    "expert": {
        "name": "Expert",
        "title": "The Knowledge Provider",
        "description": "Provides PWS methodology knowledge",
        "icon": "🎓",
        "system_prompt": """You are now in EXPERT mode. Your job is to share knowledge from the PWS methodology.

When the user asks about frameworks or methodology:
1. Explain the concept clearly
2. Give real examples (like the milkshake study for JTBD)
3. Apply it to their specific situation
4. Suggest next steps

Be a teacher, not an interrogator.
Share your knowledge generously.
Ground everything in PWS methodology.
""",
    },
    "devil": {
        "name": "Devil's Advocate",
        "title": "The Challenger",
        "description": "Stress-tests ideas and assumptions",
        "icon": "😈",
        "system_prompt": """You are now in DEVIL'S ADVOCATE mode. Your job is to constructively challenge.

Attack their assumptions:
- "What if the opposite were true?"
- "Who would disagree with this?"
- "What's the weakest part of this argument?"
- "What would have to be true for this to fail?"

Be tough but fair. The goal is to strengthen their thinking, not discourage them.
After each challenge, acknowledge what IS strong about their idea.

Format:
"Challenge: [specific challenge]
Why this matters: [implication]
How to address it: [suggestion]"
""",
    },
    "synthesizer": {
        "name": "Synthesizer",
        "title": "The Organizer",
        "description": "Structures and summarizes discussions",
        "icon": "📊",
        "system_prompt": """You are now in SYNTHESIZER mode. Your job is to organize the discussion.

Use the Minto Pyramid (SCQA) structure:
- Situation: Where are we?
- Complication: What's the problem?
- Question: What must we answer?
- Answer: What should we do?

Pull together everything discussed. Highlight the key insight.
Identify what's clear and what still needs work.

End with: "The one thing that matters most is..."
""",
    },
    "teacher": {
        "name": "Teacher",
        "title": "The Educator",
        "description": "Teaches PWS frameworks and methodologies in depth",
        "icon": "📚",
        "system_prompt": """You are now in TEACHER mode. Your job is to educate the user on PWS frameworks and innovation methodologies.

## Teaching Philosophy
- Make complex concepts accessible
- Use real-world examples liberally
- Build understanding step-by-step
- Check comprehension before moving on

## Teaching Structure
When teaching a concept:
1. **Hook**: Why this matters for them specifically
2. **Core Concept**: The big idea in one sentence
3. **Deep Dive**: Explain the framework with examples
4. **Application**: How it applies to their situation
5. **Practice**: Give them something to try

## Example Topics You Teach
- Jobs to Be Done (the milkshake study, switching costs, progress theory)
- Minto Pyramid (SCQA, grouping logic, pyramid principle)
- S-Curve Analysis (innovation cycles, jumping curves)
- Reverse Salient (bottleneck identification, Hughes' theory)
- Scenario Analysis (2x2 matrices, uncertainty mapping)
- PWS Validation (4-pillar framework, scoring rubric)

## Teaching Style
- Patient and encouraging
- Use analogies from everyday life
- Draw on the rich PWS library of case studies
- Ask "does this make sense?" periodically
- Offer to go deeper or move on based on their interest

Format:
"📚 [Concept Name]

Here's the key idea: [one sentence]

Let me explain why this matters for you: [application]

The framework works like this: [step-by-step explanation with examples]

Want me to go deeper on any part, or shall we apply this to your situation?"
""",
    },
    "pws_instructor": {
        "name": "Larry the PWS Instructor",
        "title": "The Methodology Guide",
        "description": "Step-by-step PWS methodology instruction and framework implementation",
        "icon": "🎯",
        "system_prompt": """You are now LARRY THE PWS INSTRUCTOR. Your job is to teach the PWS (Problem-Well-Stated) methodology and guide users through implementing frameworks step-by-step.

## Your Role
You are the dedicated instructor for the PWS course material. You help users:
1. Learn frameworks from the PWS curriculum
2. Apply frameworks to their specific topics (or learn them abstractly)
3. Implement methodology step-by-step with practical guidance
4. Use the tools and frameworks correctly and effectively

## Dynamic Response Length (CRITICAL)
Adjust your response length based on what the user needs:

### SHORT (100 chars) - Quick answers, confirmations, simple clarifications
- "Yes, that's the right approach."
- "JTBD = Jobs to Be Done. Want me to explain?"
- "Correct! Next step: identify the hiring criteria."

### MEDIUM (200-300 chars) - Definitions, brief explanations, single concepts
- Explaining what a framework is
- Answering a specific question
- Confirming understanding and moving forward

### LONG (400-500 chars) - Teaching a framework step, walking through application
- Explaining a complete step in a framework
- Providing an example with context
- Guiding through a specific exercise

### EXTENDED (500+ chars) - Full framework overview, comprehensive instruction
- Initial introduction to a major framework
- Complete worked example with their topic
- Synthesis of multiple concepts

## PWS Frameworks You Teach (from course material)

### Core Frameworks
1. **Jobs to Be Done (JTBD)**
   - Three job types: Functional, Emotional, Social
   - The milkshake study (Christensen)
   - Opportunity scoring: (Importance + Max(Importance - Satisfaction, 0)) / 2
   - Hiring and firing products

2. **Minto Pyramid Principle**
   - SCQA: Situation, Complication, Question, Answer
   - Pyramid structure: Answer first, then supporting arguments
   - Grouping logic: MECE (Mutually Exclusive, Collectively Exhaustive)

3. **S-Curve Analysis**
   - Technology lifecycle: Introduction → Growth → Maturity → Decline
   - Jumping S-curves for innovation
   - Identifying where you are on the curve

4. **Reverse Salient Discovery**
   - Thomas Hughes' concept from technological systems
   - Finding the bottleneck that holds back the whole system
   - Focusing innovation on the constraining element

5. **Scenario Analysis**
   - 2x2 matrix with two key uncertainties
   - Four future scenarios to plan against
   - Strategic implications for each quadrant

6. **PWS 4-Pillar Validation**
   - Pillar 1: Problem (Is it real? Who has it?)
   - Pillar 2: Solution (Does it solve it? Is it feasible?)
   - Pillar 3: Business Case (Can we make money? Is the market big enough?)
   - Pillar 4: People (Do we have the team? The capabilities?)

7. **De Bono's Six Thinking Hats**
   - White (Facts), Red (Emotions), Black (Caution)
   - Yellow (Optimism), Green (Creativity), Blue (Process)

8. **Four Lenses of Innovation**
   - Challenging orthodoxies
   - Harnessing trends
   - Leveraging resources
   - Understanding needs

## Teaching Modes

### MODE: Abstract Learning
When user wants to learn a framework without a specific topic:
"Let's learn [Framework]. Here's how it works...
[Explain with classic examples from PWS material]
Want to try it with a hypothetical case, or do you have a real topic in mind?"

### MODE: Applied Learning
When user has a specific topic:
"Let's apply [Framework] to your topic: [their topic].
Step 1: [Specific instruction]
Your turn: [What they should do]
Tell me what you come up with."

### MODE: Quick Reference
When user asks a specific question:
[Short, direct answer]
"Need more detail on this?"

### MODE: Step-by-Step Walkthrough
When user is implementing:
"Step [N] of [Framework]:
[Clear instruction]
[Example from PWS]
[How it applies to their case]
Ready for the next step?"

## Interaction Patterns

### Starting a Framework
"Which framework would you like to learn?
- JTBD (understanding customer needs)
- Minto Pyramid (structuring communication)
- S-Curve (technology lifecycle)
- Scenario Analysis (future planning)
- PWS Validation (idea assessment)
- Or tell me your challenge and I'll suggest one"

### Checking Understanding
After each major concept:
"Does this make sense? Want me to:
a) Give another example
b) Apply it to your topic
c) Move to the next step"

### Completing a Framework
"Great work! You've completed [Framework].
Key takeaways:
1. [Insight 1]
2. [Insight 2]
3. [Insight 3]

Want to:
- Apply another framework?
- Go deeper on any part?
- Move to implementation?"

## Response Guidelines
- ALWAYS ground responses in actual PWS course material
- Use the examples from the course (milkshake study, etc.)
- Be encouraging but rigorous
- Check comprehension before moving forward
- Offer both abstract and applied learning paths
- Adapt response length to the question complexity
""",
    },
}


# =============================================================================
# Helper Functions
# =============================================================================

def detect_transition_signal(message: str, session: Dict) -> Optional[str]:
    """Detect if user is signaling they want a role transition."""
    message_lower = message.lower()

    # Direct requests for answers
    answer_signals = [
        "what do you think",
        "i don't know",
        "i dont know",
        "just give me",
        "help me",
        "can you help",
        "tell me",
        "what should i",
        "what would you",
        "give me an answer",
        "stop asking",
    ]

    if any(signal in message_lower for signal in answer_signals):
        return "coach"  # Switch to helpful mode

    # Frustration signals
    frustration_signals = [
        "i already said",
        "i told you",
        "same answer",
        "i don't understand the question",
        "what else",
        "enough questions",
    ]

    if any(signal in message_lower for signal in frustration_signals):
        session["user_frustrated"] = True
        return "coach"

    # NOTE: Removed automatic 5-question limit transition
    # Instead, we'll suggest roles via UI buttons and let user decide

    # Challenge requests
    if any(word in message_lower for word in ["challenge", "critique", "wrong with", "weak"]):
        return "devil"

    # Structure requests
    if any(word in message_lower for word in ["organize", "structure", "summarize", "pull together"]):
        return "synthesizer"

    # PWS Instructor requests - step-by-step learning
    pws_instructor_signals = [
        "teach me pws",
        "learn pws",
        "pws framework",
        "walk me through",
        "step by step",
        "how do i use",
        "implement jtbd",
        "implement minto",
        "apply the framework",
        "show me how",
        "guide me through",
        "pws methodology",
        "run me through",
    ]
    if any(signal in message_lower for signal in pws_instructor_signals):
        return "pws_instructor"

    # Teaching requests - general education
    if any(word in message_lower for word in ["teach me", "explain", "how does", "what is", "learn about"]):
        return "teacher"

    # Knowledge/expertise requests
    if any(word in message_lower for word in ["methodology", "pws says", "framework"]):
        return "expert"

    return None


def suggest_roles(session: Dict, current_role: str) -> List[RoleSuggestion]:
    """
    Suggest role buttons based on conversation state.
    Human-in-the-loop: User clicks to switch, not automatic.
    """
    suggestions = []
    question_count = session.get("question_count", 0)
    clarity = session.get("clarity", {})
    messages = session.get("messages", [])

    # Check if user seems to want learning/instruction
    recent_text = " ".join([m.content.lower() for m in messages[-3:] if m.role == "user"])
    wants_learning = any(word in recent_text for word in [
        "learn", "teach", "how do i", "framework", "pws", "jtbd", "minto", "explain"
    ])

    # PWS Instructor - always show early as an option for learning
    if current_role != "pws_instructor" and (wants_learning or question_count >= 2):
        suggestions.append(RoleSuggestion(
            role_id="pws_instructor",
            name="Learn PWS",
            title="The Methodology Guide",
            reason="Step-by-step PWS framework instruction"
        ))

    # At 3+ questions, suggest synthesis/direction check
    if question_count >= 3 and current_role == "larry":
        suggestions.append(RoleSuggestion(
            role_id="synthesizer",
            name="Synthesize",
            title="The Organizer",
            reason="Let me structure what we've discussed so far"
        ))

    # At 5+ questions, strongly suggest Coach mode
    if question_count >= 5 and current_role == "larry":
        suggestions.append(RoleSuggestion(
            role_id="coach",
            name="Get Guidance",
            title="The Guide",
            reason="I've asked enough questions - let me provide direction"
        ))

    # If problem clarity is reasonable, suggest action-oriented roles
    if clarity.get("overall", 0) > 0.5:
        if current_role not in ["devil", "expert"]:
            suggestions.append(RoleSuggestion(
                role_id="devil",
                name="Challenge Me",
                title="The Challenger",
                reason="Stress-test your assumptions"
            ))
        if current_role not in ["teacher", "pws_instructor"]:
            suggestions.append(RoleSuggestion(
                role_id="teacher",
                name="Teach Me",
                title="The Educator",
                reason="Learn the relevant PWS frameworks"
            ))

    # If lots of discussion, suggest synthesis
    if len(messages) > 8 and current_role != "synthesizer":
        if not any(s.role_id == "synthesizer" for s in suggestions):
            suggestions.append(RoleSuggestion(
                role_id="synthesizer",
                name="Organize Thoughts",
                title="The Organizer",
                reason="Structure our discussion with Minto Pyramid"
            ))

    # Always offer to return to Larry if in another mode
    if current_role != "larry":
        suggestions.append(RoleSuggestion(
            role_id="larry",
            name="More Questions",
            title="The Clarifier",
            reason="Explore the problem further"
        ))

    # Limit to top 4 most relevant suggestions (increased from 3)
    return suggestions[:4]


def get_all_roles_for_ui(current_role: str) -> List[RoleInfo]:
    """
    Get all available roles formatted for UI buttons.
    User can click any of these to switch roles.
    """
    return [
        RoleInfo(
            role_id=role_id,
            name=info["name"],
            title=info["title"],
            description=info["description"],
            icon=info.get("icon", "🤖"),
            is_current=(role_id == current_role)
        )
        for role_id, info in ROLES.items()
    ]


def determine_response_length(message: str, session: Dict, current_role: str) -> int:
    """
    Dynamically determine appropriate max_tokens based on context.
    Returns max_tokens value for Claude API call.

    For PWS Instructor and teaching roles, adapts based on:
    - Question complexity
    - Whether it's an introduction vs. follow-up
    - Whether user is asking for details or quick confirmation
    """
    message_lower = message.lower()
    messages = session.get("messages", [])

    # Short responses (100-200 tokens ~ 100-200 chars)
    short_signals = [
        "yes", "no", "ok", "got it", "makes sense", "next",
        "continue", "go on", "right", "correct", "sure",
        "what's next", "and then", "proceed"
    ]
    if any(message_lower.strip() == signal or message_lower.strip().startswith(signal + " ")
           for signal in short_signals):
        return 150  # ~100 chars

    # Quick question signals
    quick_signals = ["what is", "what's", "define", "meaning of"]
    if any(signal in message_lower for signal in quick_signals) and len(message) < 50:
        return 300  # ~200-300 chars

    # Medium responses (300-400 tokens ~ 300-400 chars)
    medium_signals = [
        "how do i", "can you explain", "tell me about",
        "what does", "give me an example", "show me"
    ]
    if any(signal in message_lower for signal in medium_signals):
        return 500  # ~400 chars

    # Long responses (500+ tokens)
    long_signals = [
        "walk me through", "step by step", "teach me",
        "full explanation", "in detail", "comprehensive",
        "guide me through", "run me through", "apply",
        "implement", "let's do", "start the framework"
    ]
    if any(signal in message_lower for signal in long_signals):
        return 800  # ~500+ chars

    # Extended responses - first interaction with a framework or new topic
    if current_role == "pws_instructor":
        # Check if this is the first message in instructor mode
        instructor_messages = [m for m in messages if m.metadata and m.metadata.get("role") == "pws_instructor"]
        if len(instructor_messages) == 0:
            return 1000  # First instructor response - give full overview

    # Default based on role
    role_defaults = {
        "larry": 200,           # Short clarifying questions
        "coach": 600,           # Medium guidance
        "expert": 500,          # Medium explanations
        "teacher": 700,         # Longer teaching
        "pws_instructor": 600,  # Adaptive (but default to medium)
        "devil": 400,           # Focused challenges
        "synthesizer": 800,     # Longer synthesis
    }

    return role_defaults.get(current_role, 500)


def generate_reflection_summary(session: Dict) -> str:
    """
    Generate a Minto Pyramid reflection when reaching question threshold.
    Human-in-the-loop: Present synthesis and ask for direction.
    """
    messages = session.get("messages", [])
    clarity = session.get("clarity", {})
    question_count = session.get("question_count", 0)

    # Extract key points from conversation
    user_messages = [m.content for m in messages if m.role == "user"]

    # Simple synthesis (will be enhanced by Claude in the prompt)
    reflection = f"""
---
**Reflection Point** (after {question_count} questions)

Let me synthesize what I've understood using the Minto Pyramid (SCQA):

**Situation**: [Where we started]
**Complication**: [The challenge we've uncovered]
**Question**: [The key question we're addressing]
**Answer**: [What direction should we take?]

Current clarity scores:
- What's the problem: {clarity.get('what', 0):.0%}
- Who's affected: {clarity.get('who', 0):.0%}
- What's success: {clarity.get('success', 0):.0%}

**I'd like your input**: Should I...
1. Continue clarifying (more questions)
2. Start providing guidance (coach mode)
3. Challenge your assumptions (devil's advocate)
4. Teach relevant frameworks (teacher mode)

What would be most helpful right now?
---
"""
    return reflection


def estimate_clarity(messages: List[ChatMessage]) -> Dict[str, Any]:
    """Estimate problem clarity from conversation."""
    all_text = " ".join([m.content for m in messages if m.role == "user"]).lower()

    # Simple heuristics
    has_what = any(word in all_text for word in ["problem", "issue", "challenge", "trying to", "need to"])
    has_who = any(word in all_text for word in ["customers", "users", "people", "students", "team", "i ", "we "])
    has_success = any(word in all_text for word in ["success", "goal", "want", "should", "better", "improve"])

    what_score = 0.7 if has_what else 0.3
    who_score = 0.7 if has_who else 0.3
    success_score = 0.6 if has_success else 0.2

    return {
        "what": what_score,
        "who": who_score,
        "success": success_score,
        "overall": (what_score + who_score + success_score) / 3,
        "ready_for_value": (what_score + who_score) / 2 > 0.5,
    }


async def get_pws_context(message: str, session: Dict) -> str:
    """Get relevant PWS context from Pinecone."""
    try:
        # Get conversation context for better search
        recent_messages = session.get("messages", [])[-5:]
        context_text = " ".join([m.content for m in recent_messages if m.role == "user"])

        # Combine current message with context
        search_query = f"{message} {context_text[:200]}"

        # Search PWS Brain
        results = await pws_brain.search(search_query, top_k=3)

        if not results:
            return ""

        # Format context for injection
        context = "\n\n---\n## PWS Knowledge Context\n"
        context += "*Use this knowledge to ground your response:*\n\n"

        for i, r in enumerate(results, 1):
            framework = r.get("framework", "")
            title = r.get("title", "")
            content = r.get("content", "")[:600]  # Truncate for prompt space

            context += f"### [{i}] {title}\n"
            context += f"*Framework: {framework}*\n"
            context += f"{content}...\n\n"

        context += "---\n"
        return context

    except Exception as e:
        print(f"PWS Brain error: {e}")
        return ""


def build_system_prompt(role: str, session: Dict, pws_context: str) -> str:
    """Build the system prompt for the current role."""
    role_info = ROLES.get(role, ROLES["larry"])
    base_prompt = role_info["system_prompt"]

    # Add session state
    question_count = session.get("question_count", 0)
    clarity = session.get("clarity", {})

    state_context = f"""
## Current Session State
- Questions asked: {question_count}/5
- Problem clarity: {clarity.get('overall', 0):.0%}
- User frustrated: {session.get('user_frustrated', False)}
- Current role: {role}

## Reminder for {role_info['name']}
{'You have asked enough questions. Time to provide value!' if question_count >= 5 else ''}
{'User seems frustrated - be more direct and helpful.' if session.get('user_frustrated') else ''}
"""

    return f"{base_prompt}\n\n{state_context}\n\n{pws_context}"


# =============================================================================
# Routes
# =============================================================================

@router.post("/sessions", response_model=dict)
async def create_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "messages": [],
        "question_count": 0,
        "current_role": "larry",
        "clarity": {},
        "user_frustrated": False,
        "parked_ideas": [],
    }
    return {"session_id": session_id, "current_role": "larry"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with role switching and PWS Brain integration.
    """
    # Get or create session
    session_id = request.session_id
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "messages": [],
            "question_count": 0,
            "current_role": "larry",
            "clarity": {},
            "user_frustrated": False,
            "parked_ideas": [],
        }

    session = sessions[session_id]

    # Add user message
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow().isoformat(),
    )
    session["messages"].append(user_message)

    # Detect if we should switch roles
    current_role = session["current_role"]
    transition = detect_transition_signal(request.message, session)

    if transition and transition != current_role:
        session["current_role"] = transition
        current_role = transition

    # Get PWS Brain context
    pws_context = await get_pws_context(request.message, session)

    # Build conversation history
    history = []
    for m in session["messages"][-12:]:  # Last 12 messages
        history.append({
            "role": m.role if m.role in ["user", "assistant"] else "user",
            "content": m.content
        })

    # Build system prompt
    system_prompt = build_system_prompt(current_role, session, pws_context)

    # Determine dynamic response length based on context
    max_tokens = determine_response_length(request.message, session, current_role)

    try:
        # Call Claude with dynamic max_tokens
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=history,
        )

        response_text = response.content[0].text

        # Update session state
        if current_role == "larry":
            # Count questions (simple heuristic: if response ends with ?)
            if "?" in response_text:
                session["question_count"] = session.get("question_count", 0) + 1

        # Update clarity estimate
        session["clarity"] = estimate_clarity(session["messages"])

        # Add assistant message
        assistant_message = ChatMessage(
            role="assistant",
            content=response_text,
            timestamp=datetime.utcnow().isoformat(),
            metadata={"role": current_role}
        )
        session["messages"].append(assistant_message)

        # Suggest actions based on clarity
        suggested_actions = []
        clarity = session["clarity"]

        if clarity.get("overall", 0) > 0.6:
            suggested_actions.append("Run PWS Validation")
            suggested_actions.append("Apply JTBD Framework")

        if session["question_count"] >= 5:
            suggested_actions.append("Get structured synthesis")

        # Generate role suggestions for UI buttons (human-in-the-loop)
        suggested_roles = suggest_roles(session, current_role)

        # Get ALL roles for UI buttons (user can click any to switch)
        available_roles = get_all_roles_for_ui(current_role)

        # If we've hit 5 questions and in Larry mode, add reflection to response
        final_response = response_text
        if session["question_count"] == 5 and current_role == "larry":
            # Add reflection prompt asking for user direction
            final_response = response_text + "\n\n" + """---
**Reflection Point**

I've asked 5 clarifying questions. Let me check in with you:

I can see we're exploring something important here. Before I continue, I'd like to know what would be most helpful right now:

- **Continue exploring** - more questions to dig deeper
- **Get guidance** - I'll start offering direction based on PWS frameworks
- **Challenge my thinking** - stress-test my assumptions
- **Teach me** - explain relevant frameworks in depth
- **Synthesize** - organize what we've discussed so far

What would serve you best right now?"""

        return ChatResponse(
            session_id=session_id,
            response=final_response,
            current_role=current_role,
            question_count=session["question_count"],
            problem_clarity=session["clarity"],
            suggested_actions=suggested_actions if suggested_actions else None,
            suggested_roles=suggested_roles if suggested_roles else None,
            available_roles=available_roles,  # ALL roles for UI buttons
        )

    except Exception as e:
        return ChatResponse(
            session_id=session_id,
            response=f"I encountered an error: {str(e)}. Let me try to help anyway - what's the core of what you're trying to figure out?",
            current_role=current_role,
            question_count=session.get("question_count", 0),
            problem_clarity=session.get("clarity", {}),
            suggested_roles=None,
            available_roles=get_all_roles_for_ui(current_role),  # Still provide roles
        )


class SwitchRoleRequest(BaseModel):
    """Request to switch roles."""
    role: str


@router.post("/chat/{session_id}/switch-role")
async def switch_role(session_id: str, request: SwitchRoleRequest):
    """
    Manually switch to a different role.
    User clicks a role button in the UI, and we switch to that role.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    role = request.role
    if role not in ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown role: {role}. Valid roles: {list(ROLES.keys())}"
        )

    old_role = sessions[session_id]["current_role"]
    sessions[session_id]["current_role"] = role

    role_info = ROLES[role]
    return {
        "session_id": session_id,
        "previous_role": old_role,
        "new_role": role,
        "role_info": {
            "name": role_info["name"],
            "title": role_info["title"],
            "description": role_info["description"],
            "icon": role_info.get("icon", "🤖"),
        },
        "available_roles": get_all_roles_for_ui(role),
    }


@router.get("/roles")
async def list_roles():
    """List available roles with icons for UI buttons."""
    return {
        name: {
            "name": info["name"],
            "title": info["title"],
            "description": info["description"],
            "icon": info.get("icon", "🤖"),
        }
        for name, info in ROLES.items()
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session state."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return {
        "session_id": session_id,
        "current_role": session["current_role"],
        "question_count": session["question_count"],
        "clarity": session["clarity"],
        "message_count": len(session["messages"]),
        "available_roles": get_all_roles_for_ui(session["current_role"]),
    }


# =============================================================================
# Opportunity Management - Bank of Opportunities
# =============================================================================

class Opportunity(BaseModel):
    """
    An opportunity extracted from a conversation.
    This is what gets saved to the "Bank of Opportunities" for further deep dives.
    """
    id: Optional[str] = None
    title: str
    description: str
    problem_statement: Optional[str] = None  # The "What" from conversation
    target_audience: Optional[str] = None    # The "Who" from conversation
    success_criteria: Optional[str] = None   # The "Success" from conversation
    status: str = "exploring"  # exploring, validated, parked, archived
    tags: List[str] = []
    pws_score: Optional[float] = None  # 0-100 based on PWS 4-pillar validation
    deep_dive_count: int = 0
    created_from_session: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateOpportunityRequest(BaseModel):
    """Request to create an opportunity from a conversation."""
    session_id: str
    title: Optional[str] = None  # If not provided, will be generated from conversation
    tags: Optional[List[str]] = None


# In-memory opportunity storage (would be Neo4j in production)
opportunities: Dict[str, Opportunity] = {}


@router.post("/opportunities/create-from-session")
async def create_opportunity_from_session(request: CreateOpportunityRequest):
    """
    Create an opportunity from the current conversation session.

    This is how insights from a Larry conversation become opportunities
    in the Bank of Opportunities for further deep dives.

    The opportunity captures:
    - Problem statement (the "What")
    - Target audience (the "Who")
    - Success criteria (what better looks like)
    - Clarity scores from the conversation
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[request.session_id]
    messages = session.get("messages", [])
    clarity = session.get("clarity", {})

    # Extract key information from conversation
    user_messages = [m.content for m in messages if m.role == "user"]
    all_user_text = " ".join(user_messages)

    # Generate title if not provided
    title = request.title
    if not title:
        # Use first significant user message as title basis
        for msg in user_messages:
            if len(msg) > 20:
                title = msg[:100] + "..." if len(msg) > 100 else msg
                break
        if not title:
            title = "Untitled Opportunity"

    # Create the opportunity
    opp_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    opportunity = Opportunity(
        id=opp_id,
        title=title,
        description=all_user_text[:500] if all_user_text else "No description",
        problem_statement=f"Clarity: {clarity.get('what', 0):.0%}" if clarity else None,
        target_audience=f"Clarity: {clarity.get('who', 0):.0%}" if clarity else None,
        success_criteria=f"Clarity: {clarity.get('success', 0):.0%}" if clarity else None,
        status="exploring",
        tags=request.tags or [],
        pws_score=clarity.get("overall", 0) * 100 if clarity else None,
        deep_dive_count=0,
        created_from_session=request.session_id,
        created_at=now,
        updated_at=now,
    )

    opportunities[opp_id] = opportunity

    return {
        "message": "Opportunity created successfully",
        "opportunity": opportunity,
        "next_steps": [
            "Run PWS Validation to get a proper score",
            "Apply JTBD framework to understand customer needs",
            "Use Devil's Advocate to stress-test assumptions",
        ]
    }


@router.get("/opportunities")
async def list_opportunities():
    """List all opportunities in the Bank of Opportunities."""
    return {
        "total": len(opportunities),
        "opportunities": list(opportunities.values()),
        "by_status": {
            "exploring": len([o for o in opportunities.values() if o.status == "exploring"]),
            "validated": len([o for o in opportunities.values() if o.status == "validated"]),
            "parked": len([o for o in opportunities.values() if o.status == "parked"]),
        }
    }


@router.get("/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    """Get a specific opportunity."""
    if opportunity_id not in opportunities:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunities[opportunity_id]


@router.post("/opportunities/{opportunity_id}/deep-dive")
async def start_deep_dive(opportunity_id: str):
    """
    Start a deep dive session for an opportunity.
    Creates a new chat session pre-loaded with the opportunity context.
    """
    if opportunity_id not in opportunities:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp = opportunities[opportunity_id]

    # Create a new session for the deep dive
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "messages": [],
        "question_count": 0,
        "current_role": "larry",  # Start with Larry
        "clarity": {},
        "user_frustrated": False,
        "parked_ideas": [],
        "opportunity_id": opportunity_id,  # Link to the opportunity
        "is_deep_dive": True,
    }

    # Increment deep dive count
    opp.deep_dive_count += 1
    opp.updated_at = datetime.utcnow().isoformat()

    return {
        "session_id": session_id,
        "opportunity": opp,
        "context": f"Deep diving into: {opp.title}",
        "suggested_starting_points": [
            "Let's validate the problem statement",
            "Who exactly is the target customer?",
            "What does success look like for this?",
            "Challenge the core assumptions",
        ],
        "available_roles": get_all_roles_for_ui("larry"),
    }


@router.patch("/opportunities/{opportunity_id}")
async def update_opportunity(opportunity_id: str, updates: Dict[str, Any]):
    """Update an opportunity (status, tags, scores, etc.)."""
    if opportunity_id not in opportunities:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp = opportunities[opportunity_id]

    # Update allowed fields
    allowed_fields = ["title", "description", "status", "tags", "pws_score",
                      "problem_statement", "target_audience", "success_criteria"]

    for field, value in updates.items():
        if field in allowed_fields:
            setattr(opp, field, value)

    opp.updated_at = datetime.utcnow().isoformat()

    return opp
