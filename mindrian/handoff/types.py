"""
Handoff Types and Modes

Defines the vocabulary for agent handoffs in Mindrian.
"""

from enum import Enum


class HandoffType(str, Enum):
    """
    Types of agent handoffs.

    DELEGATE: Orchestrator assigns work, expects results returned
              - Larry → Framework → Larry
              - Maintains orchestrator control
              - Most common pattern

    TRANSFER: Full control passes to another agent
              - Larry → Expert Agent (user talks to expert)
              - Used when deep expertise needed
              - Less common, explicit user consent

    RETURN: Agent completes and returns to caller
            - Framework → Larry
            - Always includes results/output
            - Triggers synthesis step

    ESCALATE: Problem beyond current agent's capability
              - Any Agent → Larry → User
              - Requires human input
              - Includes explanation of blocker
    """

    DELEGATE = "delegate"      # Assign work, get results back
    TRANSFER = "transfer"      # Full control transfer
    RETURN = "return"          # Complete and return
    ESCALATE = "escalate"      # Need human help


class HandoffMode(str, Enum):
    """
    How work is distributed during delegation.

    SEQUENTIAL: One agent at a time, each builds on previous
               - Agent A → Agent B → Agent C
               - Output of A feeds into B
               - Best for: pipelines, refinement

    PARALLEL: All agents work simultaneously
              - Agent A + Agent B + Agent C
              - Results combined at end
              - Best for: multiple perspectives

    SELECTIVE: Orchestrator chooses best agent
               - Route to Agent A OR B OR C
               - Based on problem type
               - Best for: specialized routing

    DEBATE: Agents take opposing positions
            - Agent A argues FOR
            - Agent B argues AGAINST
            - Synthesis resolves
            - Best for: decision support
    """

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    SELECTIVE = "selective"
    DEBATE = "debate"


class ReturnBehavior(str, Enum):
    """
    What happens when delegated work completes.

    SYNTHESIZE: Orchestrator combines and interprets results
                - Default behavior
                - Larry reads outputs, creates summary
                - Best for: complex analyses

    PASSTHROUGH: Raw results returned to user
                 - No orchestrator interpretation
                 - Framework output shown directly
                 - Best for: structured outputs (scorecards)

    ITERATE: Results trigger another delegation round
             - Larry reviews, decides next framework
             - Continues until complete
             - Best for: deep exploration
    """

    SYNTHESIZE = "synthesize"
    PASSTHROUGH = "passthrough"
    ITERATE = "iterate"
