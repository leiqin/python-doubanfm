# copy from _MozillaCookieJar.py
# -*- coding: utf-8 -*-

import time
import cookielib

from cookielib import (_warn_unhandled_exception, FileCookieJar, LoadError,
                       Cookie, MISSING_FILENAME_TEXT)

class FirecookieCookieJar(FileCookieJar):

    timeformat = '%a, %d %b %Y %H:%M:%S %Z'

    def _really_load(self, f, filename, ignore_discard, ignore_expires):
        now = time.time()

        try:
            while 1:
                line = f.readline()
                if line == "": break

                # last field may be absent, so keep any trailing tab
                if line.endswith("\n"): line = line[:-1]

                # skip comments and blank lines XXX what is $ for?
                if (line.strip().startswith(("#", "$")) or
                    line.strip() == ""):
                    continue

#                domain, domain_specified, path, secure, expires, name, value = \
#                        line.split("\t")

                arr = line.strip().split("\t")

                domain = arr.pop(0)
                domain_specified = arr.pop(0)
                path = arr.pop(0)
                secure = arr.pop(0)
                expires = arr.pop(0)

                name = arr.pop(0)
                if arr:
                    value = arr.pop(0)
                else:
                    value = None

                secure = (secure == "TRUE")
                domain_specified = (domain_specified == "TRUE")

                initial_dot = domain.startswith(".")
                assert domain_specified == initial_dot

                discard = False
                if expires == None:
                    expires = None
                    discard = True

                # assume path_specified is false
                c = Cookie(0, name, value,
                           None, False,
                           domain, domain_specified, initial_dot,
                           path, False,
                           secure,
                           expires,
                           discard,
                           None,
                           None,
                           {})
                if not ignore_discard and c.discard:
                    continue
                if not ignore_expires and c.is_expired(now):
                    continue
                self.set_cookie(c)

        except IOError:
            raise
        except Exception:
            _warn_unhandled_exception()
            raise LoadError("invalid Netscape format cookies file %r: %r" %
                            (filename, line))

    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError(MISSING_FILENAME_TEXT)

        f = open(filename, "w")
        try:
            now = time.time()
            for cookie in self:
                if not ignore_discard and cookie.discard:
                    continue
                if not ignore_expires and cookie.is_expired(now):
                    continue
                if cookie.secure: secure = "TRUE"
                else: secure = "FALSE"
                if cookie.domain.startswith("."): initial_dot = "TRUE"
                else: initial_dot = "FALSE"
                if cookie.expires is not None:
                    expires = str(cookie.expires)
                else:
                    expires = "0"
                if cookie.value is None:
                    # cookies.txt regards 'Set-Cookie: foo' as a cookie
                    # with no name, whereas cookielib regards it as a
                    # cookie with no value.
                    name = ""
                    value = cookie.name
                else:
                    name = cookie.name
                    value = cookie.value
                f.write(
                    "\t".join([a for a in [cookie.domain, initial_dot, cookie.path,
                               secure, expires, name, value] if a ])+
                    "\n")
        finally:
            f.close()

    
    # 不清除过期的cookie
    clearExpried = False
    def clear_expired_cookies(self):
        if self.clearExpried:
            cookielib.CookieJar.clear_expired_cookies(self)

class MyCookiePolicy(cookielib.DefaultCookiePolicy):

    def return_ok(self, cookie, request):

        # 不验证是否过期
        # for n in "version", "verifiability", "secure", "expires", "port", "domain":
        for n in "version", "verifiability", "secure", "port", "domain":
            fn_name = "return_ok_"+n
            fn = getattr(self, fn_name)
            if not fn(cookie, request):
                return False
        return True

