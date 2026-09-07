import logging
import sys

#get logger
logger = logging.getLogger()  #can give name or leave it  empty 

#create formatter- this is how the logs output will look like
formatter = logging.Formatter(
    fmt= "%(asctime)s - %(levelname)s - %(message)s"
)   #url and method  and process type are part of extra = log_dict

#create handlers 
stream_handler = logging.StreamHandler(sys.stdout) #logs of streamhandler go to stdout
file_handler = logging.FileHandler('app.log') #logs of file handler go to app.log

stream_handler.setFormatter(formatter)   # ← missing before
file_handler.setFormatter(formatter)     # ← missing before


#add handlers to the logger
logger.handlers=[stream_handler,file_handler]

#set level to logger
logger.setLevel(logging.INFO)