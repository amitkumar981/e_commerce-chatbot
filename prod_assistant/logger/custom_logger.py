import logging 
from datetime import datetime
import structlog
import os

class CustomLogger:
    def __init__(self,log_dir="logs"):
        #ensure log directory exists
        self.log_dir = os.path.join(os.getcwd(),log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        
        #Timestamp of logfile
        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        self.logfile_path = os.path.join(self.log_dir,log_file)
        
    def get_logger(self,name=__name__):
        #get the basename only from path 
        logger_name = os.path.basename(name)
        
        #configure file handler
        file_handler = logging.FileHandler(self.logfile_path)
        file_handler.setLevel(logging.INFO) #log only info level and above
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        #configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s")) #only write the actual messages
        
        #setup the basic  logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[file_handler,console_handler]
        )
        
        #configure the structure log'
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"), # add timestamp in iso format
                structlog.processors.add_log_level, # add level field tp show log level
                structlog.processors.EventRenamer("event"), # rename main log messages to event
                structlog.processors.JSONRenderer(), # convert everything into json
            ],
            logger_factory = structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use = True
        )
        
        return structlog.get_logger(logger_name)
    
    #test
if __name__ =="__main__":
    logger = CustomLogger().get_logger(__file__)
    logger.info("Test log message",user_id =123,filename="report.pdf")
    logger.error("Test error message", user_id =123,error="file not found")