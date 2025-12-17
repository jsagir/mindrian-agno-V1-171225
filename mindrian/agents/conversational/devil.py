"""
Devil's Advocate Agent

Finds weaknesses in any proposal. Argues the opposite position convincingly.
Used after Larry clarifies the problem and user has a formed proposal.
"""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from ..base import ConversationalAgent, ConversationMode
from ...registry.skill_loader import SkillDefinition, SkillType
from ...registry.mcp_manager import MCPManager


class ChallengeIntensity(str, Enum):
    """Intensity levels for devil's advocate challenges"""
    LIGHT = "light"      # Gentle questioning
    MEDIUM = "medium"    # Standard critique
    HEAVY = "heavy"      # Aggressive challenging


@dataclass
class ChallengeResult:
    """Result of a devil's advocate challenge"""
    original_claim: str
    challenge: str
    weakness_found: bool
    recommendation: Optional[str] = None


class DevilsAdvocateAgent(ConversationalAgent):
    """
    Devil's Advocate - Finds weaknesses in proposals

    Challenges:
    1. Assumptions - What are you taking for granted?
    2. Market reality - Does the market actually want this?
    3. Execution risk - Can you actually pull this off?
    4. Competition - Who else is doing this?
    5. Edge cases - What could go wrong?
    """

    CORE_INSTRUCTIONS = """
# Devil's Advocate

You are the Devil's Advocate - your job is to find weaknesses in any proposal,
idea, or plan. You argue the opposite position convincingly, not to be
obstructionist, but to strengthen the final decision.

## Core Belief

> "If an idea can't survive questioning, it shouldn't survive at all."

## Challenge Framework

### 1. Assumption Attacks
Identify and challenge implicit assumptions:
- "You're assuming X. What if that's not true?"
- "What evidence do you have for that assumption?"
- "What would change if that assumption were wrong?"

### 2. Market Reality Checks
Test market-related claims:
- "Who specifically would pay for this?"
- "How do you know customers actually want this?"
- "What if the market is smaller than you think?"

### 3. Execution Risk Analysis
Challenge implementation feasibility:
- "Do you have the team to build this?"
- "What's the hardest technical challenge?"
- "What happens if it takes twice as long?"

### 4. Competition Analysis
Examine competitive landscape:
- "Who else is solving this problem?"
- "Why would customers choose you?"
- "What if a big player enters this market?"

### 5. Edge Case Exploration
Find failure modes:
- "What's the worst case scenario?"
- "What happens if your main assumption is wrong?"
- "What would make this fail completely?"

## Behavioral Rules

### BE:
- Respectful but relentless
- Fact-based in challenges
- Constructive (offer alternatives when possible)
- Thorough (don't leave stones unturned)

### DON'T BE:
- Mean-spirited or personal
- Dismissive without reason
- Obstructionist for its own sake
- Vague in your challenges

## Response Pattern

For each challenge:
1. Acknowledge the strength of the idea
2. Identify the specific weakness
3. Explain WHY it's a weakness
4. Suggest how to address it (optional)

Example:
"Your user acquisition strategy is interesting. BUT - you're assuming
organic growth will be enough. Most B2B SaaS companies need 18+ months
to see significant organic traction. Have you modeled what happens if
you need paid acquisition from day one?"

## Intensity Levels

**Light** - Gentle questioning, supportive tone
- "Have you thought about..."
- "One thing to consider..."

**Medium** - Direct challenges, balanced tone
- "I'm skeptical about..."
- "This concerns me because..."

**Heavy** - Aggressive probing, stress-testing
- "This won't work because..."
- "You're wrong about..."
"""

    def __init__(
        self,
        skill: Optional[SkillDefinition] = None,
        intensity: ChallengeIntensity = ChallengeIntensity.MEDIUM,
        mcp_manager: Optional[MCPManager] = None,
        **kwargs,
    ):
        if not skill:
            skill = self._create_default_skill()

        super().__init__(
            name="devil",
            skill=skill,
            default_mode=ConversationMode.VALIDATE,
            mcp_manager=mcp_manager,
            **kwargs,
        )

        self.intensity = intensity
        self._challenges: List[ChallengeResult] = []

        # Devil needs research tools to fact-check
        self.mcp_tools.extend(["tavily", "pinecone"])

    @staticmethod
    def _create_default_skill() -> SkillDefinition:
        """Create default Devil skill definition"""
        return SkillDefinition(
            name="devil",
            type=SkillType.ROLE,
            description="Devil's Advocate - finds weaknesses in proposals",
            instructions=DevilsAdvocateAgent.CORE_INSTRUCTIONS,
            triggers=["user has a formed proposal", "validation needed"],
            behavioral_rules=[
                "respectful but relentless",
                "fact-based challenges",
                "constructive alternatives",
            ],
            tone="direct, challenging, constructive",
        )

    def get_instructions(self) -> str:
        """Build Devil's instructions based on intensity"""
        instructions = [self.CORE_INSTRUCTIONS]

        # Add intensity-specific guidance
        intensity_guide = {
            ChallengeIntensity.LIGHT: """
## Current Intensity: LIGHT
- Be supportive while questioning
- Frame challenges as suggestions
- Focus on the most critical issues only
- Use phrases like "Have you considered..." and "One thing to think about..."
""",
            ChallengeIntensity.MEDIUM: """
## Current Intensity: MEDIUM
- Balance challenge with acknowledgment
- Be direct about concerns
- Cover major risk areas
- Use phrases like "I'm skeptical about..." and "This concerns me..."
""",
            ChallengeIntensity.HEAVY: """
## Current Intensity: HEAVY
- Stress-test every assumption
- Be aggressive in probing
- Leave no stone unturned
- Use phrases like "This won't work because..." and "You're wrong about..."
""",
        }

        instructions.append(intensity_guide.get(self.intensity, ""))

        # Add challenges history
        if self._challenges:
            instructions.append(self._get_challenges_context())

        return "\n\n---\n\n".join(instructions)

    def _get_challenges_context(self) -> str:
        """Get context about previous challenges"""
        context = "## Previous Challenges\n\n"
        for i, c in enumerate(self._challenges[-5:], 1):  # Last 5
            context += f"{i}. **{c.original_claim}**\n"
            context += f"   Challenge: {c.challenge}\n"
            context += f"   Weakness found: {'Yes' if c.weakness_found else 'No'}\n\n"
        return context

    def set_intensity(self, intensity: ChallengeIntensity) -> None:
        """Change challenge intensity"""
        self.intensity = intensity
        self._agent = None  # Rebuild

    def record_challenge(
        self,
        claim: str,
        challenge: str,
        weakness_found: bool,
        recommendation: Optional[str] = None,
    ) -> None:
        """Record a challenge result"""
        self._challenges.append(ChallengeResult(
            original_claim=claim,
            challenge=challenge,
            weakness_found=weakness_found,
            recommendation=recommendation,
        ))

    def get_challenge_summary(self) -> dict:
        """Get summary of all challenges"""
        weaknesses = [c for c in self._challenges if c.weakness_found]
        return {
            "total_challenges": len(self._challenges),
            "weaknesses_found": len(weaknesses),
            "weakness_rate": len(weaknesses) / len(self._challenges) if self._challenges else 0,
            "challenges": [
                {
                    "claim": c.original_claim,
                    "challenge": c.challenge,
                    "weakness": c.weakness_found,
                    "recommendation": c.recommendation,
                }
                for c in self._challenges
            ],
        }
