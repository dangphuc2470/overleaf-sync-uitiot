"""Ol Browser Login Utility"""
##################################################
# MIT License
##################################################
# File: olbrowserlogin.py
# Description: Overleaf Browser Login Utility
# Author: Moritz Glöckl
# License: MIT
# Version: 1.2.0
##################################################

from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtWebEngineWidgets import *
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage

# Where to get the CSRF Token and where to send the login request to
LOGIN_URL = "https://latex.uitiot.vn/login"
PROJECT_URL = "https://latex.uitiot.vn/project"  # The dashboard URL
# JS snippet to extract the csrfToken
JAVASCRIPT_CSRF_EXTRACTOR = "document.getElementsByName('ol-csrfToken')[0].content"
# Name of the cookies we want to extract
COOKIE_NAMES = ["overleaf_session2", "GCLB", "overleaf.sid"]


class OlBrowserLoginWindow(QMainWindow):
    """
    Overleaf Browser Login Utility
    Opens a browser window to securely login the user and returns relevant login data.
    """

    def __init__(self, keep_open=False, *args, **kwargs):
        super(OlBrowserLoginWindow, self).__init__(*args, **kwargs)

        self.webview = QWebEngineView()
        self.keep_open = keep_open

        self._cookies = {}
        self._csrf = ""
        self._login_success = False

        self.profile = QWebEngineProfile(self.webview)
        self.cookie_store = self.profile.cookieStore()
        self.cookie_store.cookieAdded.connect(self.handle_cookie_added)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)

        self.profile.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)

        webpage = QWebEnginePage(self.profile, self)
        self.webview.setPage(webpage)
        self.webview.load(QUrl.fromUserInput(LOGIN_URL))
        self.webview.loadFinished.connect(self.handle_load_finished)

        self.setCentralWidget(self.webview)
        self.resize(600, 700)

    def handle_load_finished(self):
        current_url = self.webview.url().toString()
        print(f"🌐 Page loaded: {current_url}")
        
        def callback(result):
            print(f"🔑 CSRF extraction result: {result}")
            self._csrf = result
            self._login_success = True
            print(f"🍪 Final cookies captured: {list(self._cookies.keys())}")
            if not self.keep_open:
                QCoreApplication.quit()
            else:
                print("Login successful! You can now close the browser window manually or continue browsing.")

        if current_url == PROJECT_URL:
            print("✅ On projects page, extracting CSRF token...")
            # Try multiple ways to extract CSRF token
            csrf_script = """
            (function() {
                // Method 1: meta tag with name ol-csrfToken
                var meta1 = document.getElementsByName('ol-csrfToken')[0];
                if (meta1) return meta1.content;
                
                // Method 2: meta tag with name _csrf
                var meta2 = document.getElementsByName('_csrf')[0];
                if (meta2) return meta2.content;
                
                // Method 3: input with name _csrf
                var input = document.querySelector('input[name="_csrf"]');
                if (input) return input.value;
                
                // Method 4: check window variables
                if (typeof window.csrfToken !== 'undefined') return window.csrfToken;
                
                return 'CSRF_NOT_FOUND';
            })();
            """
            self.webview.page().runJavaScript(csrf_script, 0, callback)
        else:
            print(f"⏳ Not on projects page yet, current: {current_url}")

    def handle_cookie_added(self, cookie):
        cookie_name = cookie.name().data().decode('utf-8')
        cookie_value = cookie.value().data().decode('utf-8')
        cookie_domain = cookie.domain()
        
        # Debug: Print all cookies being added
        print(f"🍪 Cookie added: {cookie_name} = {cookie_value[:20]}... (domain: {cookie_domain})")
        
        if cookie_name in COOKIE_NAMES:
            self._cookies[cookie_name] = cookie_value
            print(f"✅ Captured target cookie: {cookie_name}")
        else:
            # Show all cookies that might be relevant
            if 'session' in cookie_name.lower() or 'auth' in cookie_name.lower() or 'overleaf' in cookie_name.lower():
                print(f"🔍 Potential session cookie: {cookie_name} = {cookie_value[:20]}...")
                # Also capture potential session cookies
                self._cookies[cookie_name] = cookie_value

    @property
    def cookies(self):
        return self._cookies

    @property
    def csrf(self):
        return self._csrf

    @property
    def login_success(self):
        return self._login_success


def login(keep_open=False):
    from PySide6.QtCore import QLoggingCategory, QTimer
    QLoggingCategory.setFilterRules('''\
    qt.webenginecontext.info=false
    ''')

    app = QApplication([])
    ol_browser_login_window = OlBrowserLoginWindow(keep_open=keep_open)
    ol_browser_login_window.show()
    
    if keep_open:
        # Add a timer to check login status periodically when keeping browser open
        timer = QTimer()
        def check_login_status():
            if ol_browser_login_window.login_success:
                timer.stop()
                # Don't quit automatically when keeping browser open
                print("Login completed! Browser will remain open.")
        
        timer.timeout.connect(check_login_status)
        timer.start(1000)  # Check every second
    
    app.exec()

    if not ol_browser_login_window.login_success:
        return None

    return {"cookie": ol_browser_login_window.cookies, "csrf": ol_browser_login_window.csrf}
