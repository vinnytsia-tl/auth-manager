import os
import sys

sys.path.insert(2, os.path.join(sys.base_prefix, 'DLLs'))

# pylint: disable=wrong-import-position

import socket

import servicemanager
import win32event
import win32service
import win32serviceutil

from main_bot import main_bot

# pylint: enable=wrong-import-position

class AuthBotSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "AuthBotSvc"
    _svc_display_name_ = "Auth manager bot Service"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        main_bot()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AuthBotSvc)
