import sys
import trace
from typing import Optional,cast
import traceback

class ProductAssistantException(Exception):
    def __init__(self,error_message,error_detail: Optional[object] = None):
        
        #normalize message
        if isinstance(error_detail,BaseException):
            norm_message  = str(error_message)
        else:
            norm_message = str(error_message) 
        
        exc_type =  exc_value = exc_tb = None
        
        if error_detail is None:
            exc_type, exc_value, exc_tb = sys.exc_info()
        else:
            if hasattr(error_detail,"exc_info"):
                exc_info_object = cast(sys,error_detail)
                exc_type, exc_value, exc_tb = exc_info_object.exc_info()
            elif isinstance(error_detail,BaseException):
                exc_type = type(error_detail)
                exc_value = error_detail
                exc_tb = error_detail.__traceback__
            else:
                
                exc_type, exc_value, exc_tb = sys.exc_info()
            # Walk to the last frame to report the most relevant location
            last_tb = exc_tb
            while last_tb and last_tb.tb_next:
                last_tb = last_tb.tb_next
            
            self.filename = last_tb.tb_frame.f_code.co_filename if last_tb else  "<unknown>" #get the filename
            self.lineno = last_tb.tb_lineno if last_tb else -1 # get the line number from file
            self.error_message = norm_message
            
            if exc_type and exc_tb:
                self.traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
            else:
                self.traceback_str = "No traceback available"
            
            super().__init__(self.__str__())
        
        def __str__(self):
            #compact =: logger friendly message
            base = f"Error in [{self.filename}, at line {self.lineno},message = {self.error_message!r}"
            if self.traceback_str:
                return f"{base}, Traceback: {self.traceback_str}"
            return base
        def __repr__(self):
            return f"ProductAssistantException(file={self.filename} ,line = {self.lineno},message = {self.error_message!r}"
        
# if __name__ == "__main__":
#     # Demo-1: generic exception -> wrap
#     try:
#         a = 1 / 0
#     except Exception as e:
#         raise ProductAssistantException("Division failed",e) from e

    # Demo-2: still supports sys (old pattern)
    # try:
    #     a = int("abc")
    # except Exception as e:
    #     raise DocumentPortalException(e, sys)
        
            
            
                
        