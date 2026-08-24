from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    total: int
    skip: int
    limit: int
    items: List[T]


"""" let's use plain numbers instead of code. Imagine your Users table has 50 people in it, numbered 1 to 50 in order.

limit = how many you want to see at once. Say limit=20 → show 20 at a time.

skip = how many to skip over before you start counting those 20.

Page 1
skip=0, limit=20 → skip nothing, take the next 20 → you get people 1–20

Page 2
skip=20, limit=20 → skip the first 20 (1–20), then take the next 20 → you get people 21–40

Page 3
skip=40, limit=20 → skip the first 40 (1–40), then take the next 20 → you get people 41–50 (only 10 left, since there are only 50 total)

So the pattern for "page number" → skip is:

page 1 → skip = 0
page 2 → skip = 20
page 3 → skip = 40
page 4 → skip = 60
Formula: skip = (page_number - 1) × limit

That's it — skip/limit is just "how far in do I start" + "how many do I grab from there." The frontend is the one that turns this into "Page 1, 2, 3" buttons; your backend only ever needs to understand skip and limit, nothing about "page numbers" directly.

Does that land, or is it still fuzzy — want me to also show what the actual SQL looks like underneath (OFFSET/LIMIT in plain SQL) to see it from one more angle?"""