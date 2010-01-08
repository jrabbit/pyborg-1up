# msnp.py -- An implementation of the MSN Messenger Protocol
#
# Version 0.4 (for Python 2.3)
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

"""An implementation of the MSN Messenger Protocol

msnp is a library, written in object-oriented Python, for accessing the MSN
instant messaging service.

To use this module for instant messaging, an instance of the msnp.Session class
must be created.  The msnp.SessionCallbacks interface must be implemented by
the client.  For example:

    import msnp

    class MyCallbacks(msnp.SessionCallbacks):
        def state_changed(self, state):
            print 'New state:', state

    im = msnp.Session(MyCallbacks())
    im.login('gill_bates@hotmail.com', 'microshaft')

If the login succeeds, the state_changed method of the MyCallbacks instance
will be called, and 'New state: NLN' will get printed.

For more information, visit:
http://msnp.sourceforge.net/
"""

# Note about documentation:  All public objects (classes, methods, globals,
# etc.) have been documented with Python docstrings; private code has been
# sprinkled with terse comments.

from error import Error
from friend import Group, Friend, FriendList

from chat import Chat, ChatCallbacks
from session import Session, SessionCallbacks

from protocol import States, Lists, PrivacyModes

import protocol

__all__ = [
    'Error',
    'Group', 'Friend', 'FriendList',
    'Chat', 'ChatCallbacks',
    'Session', 'SessionCallbacks',
    'States', 'Lists', 'PrivacyModes',
]

# vim: set ts=4 sw=4 et tw=79 :

