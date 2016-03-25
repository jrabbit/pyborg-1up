# protocol.py -- States, Lists, PrivacyModes classes, and errors global
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

class States:
    """Presence states"""
    ONLINE = 'NLN'
    OFFLINE = 'FLN'
    INVISIBLE = 'HDN'
    BUSY = 'BSY'
    IDLE = 'IDL'
    BE_RIGHT_BACK = 'BRB'
    AWAY = 'AWY'
    ON_THE_PHONE = 'PHN'
    OUT_TO_LUNCH = 'LUN'

class Lists:
    """Types of friend lists"""
    FORWARD = 'FL'
    REVERSE = 'RL'
    ALLOW = 'AL'
    BLOCK = 'BL'

class PrivacyModes:
    """Privacy modes"""
    ALLOW = 'AL'
    BLOCK = 'BL'

list_flags = {
    Lists.FORWARD : 1,
    Lists.ALLOW   : 2,
    Lists.BLOCK   : 4,
    Lists.REVERSE : 8,
}

errors = {
    '200': 'Syntax error',
    '201': 'Invalid parameter',
    '205': 'Invalid user',
    '206': 'Domain name missing',
    '207': 'Already logged in',
    '208': 'Invalid username',
    '209': 'Invalid fusername',
    '210': 'User list full',
    '215': 'User already there',
    '216': 'User already on list',
    '217': 'User not online',
    '218': 'Already in mode',
    '219': 'User is in the opposite list',
    '219': 'User is in the opposite list',
    '231': 'Tried to add a contact to a group that doesn\'t exist',
    '280': 'Switchboard failed',
    '281': 'Transfer to switchboard failed',

    '300': 'Required field missing',
    '302': 'Not logged in',

    '500': 'Internal server error',
    '501': 'Database server error',
    '510': 'File operation failed',
    '520': 'Memory allocation failed',
    '540': 'Wrong CHL value sent to server',

    '600': 'Server is busy',
    '601': 'Server is unavaliable',
    '602': 'Peer nameserver is down',
    '603': 'Database connection failed',
    '604': 'Server is going down',

    '707': 'Could not create connection',
    '710': 'CVR parameters either unknown or not allowed',
    '711': 'Write is blocking',
    '712': 'Session is overloaded',
    '713': 'Too many active users',
    '714': 'Too many sessions',
    '715': 'Not expected',
    '717': 'Bad friend file',

    '911': 'Authentication failed',
    '913': 'Not allowed when offline',
    '920': 'Not accepting new users',
    '924': 'Passport account not yet verified',
}

# vim: set ts=4 sw=4 et tw=79 :

