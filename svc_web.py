import os
import sys

sys.path.insert(2, os.path.join(sys.base_prefix, 'DLLs'))

# pylint: disable=wrong-import-position

import socket  # noqa:E402

import servicemanager  # noqa:E402
import win32event  # noqa:E402
import win32service  # noqa:E402
import win32serviceutil  # noqa:E402

from main_web import exit_web, main_web  # noqa:E402

# pylint: enable=wrong-import-position


class AuthWebSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "AuthWebSvc"
    _svc_display_name_ = "Auth manager web Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        exit_web()

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        main_web()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AuthWebSvc)
