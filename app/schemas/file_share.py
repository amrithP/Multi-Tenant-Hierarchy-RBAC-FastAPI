from pydantic import BaseModel


from typing import List




class SharedWithEntry(BaseModel):
    user_id: int
    can_edit: bool = False


class UpdateSharesRequest(BaseModel):
    shared_with: List[SharedWithEntry]


"""can_edit: bool = False means: if whoever calls POST /files/{id}/share doesn't explicitly include can_edit in the request body, it defaults to False (view-only) rather than True (edit access).

Why default to the more restrictive option

This is a deliberate safety choice, not an arbitrary one — it's called the "principle of least privilege": when access level isn't specified, grant the minimum necessary, not the maximum. If it defaulted to True instead, then anyone calling the share endpoint without thinking to add can_edit would accidentally hand out full edit rights — a much worse mistake to make by accident than accidentally granting only view access.

Concretely
{"user_id": 2}

→ shares with user 2, view-only (since can_edit wasn't included, it falls back to False).

{"user_id": 2, "can_edit": true}

→ shares with user 2, with edit rights, because it was explicitly asked for.

So the Owner has to deliberately opt in to giving someone edit access; view-only is the safe fallback if they forget or don't care to specify. Same reasoning as why passwords default to "not visible" until you click the eye icon, or why new files on most systems default to private rather than public — the safer state is the default, and the riskier state requires an explicit choice."""