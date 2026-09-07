from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

#get_remote_address means the limit is tracked per IP address — so it's "this specific computer can only try 5 times a minute," not a global limit shared by everyone.