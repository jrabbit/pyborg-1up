# error.py -- Error class(es)
#
# Copyright (C) 2003 Manish Jethani (manish_jethani AT yahoo.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

class Error:
    """Generic exception type"""
    def __init__(self, code, message):
        self.code = code
        self.message = message
    def __str__(self):
        return str(self.code) + ':' + self.message

class HttpError(Error):
    """Error returned from HTTP server"""
    def __init__(self, code, message, http_status, http_reason):
        Error.__init__(self, code, message)
        self.http_status = http_status
        self.http_reason = http_reason
    def __str__(self):
        return Error.__str__(self) \
        + '[%s:%s]' % (str(self.http_status), self.http_reason)

# vim: set ts=4 sw=4 et tw=79 :

