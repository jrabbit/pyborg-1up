# friend.py -- Group, Friend, FriendList classes
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

from protocol import States, Lists, PrivacyModes
from time import time

class Group:
    """A group in the friend list"""
    def __init__(self, id, name, friends = None):
        self.id = id
        self.name = name
        if friends == None:
            friends = {}
        self.friends = friends

    def size(self):
        """Return number of friends in this group"""
        return len(self.friends)

    def get_id(self):
        """Return ID of this group"""
        return self.id

    def get_name(self):
        """Return name of this group"""
        return self.name

    def get_friend(self, passport_id):
        """Return friend in this group

        Keyword arguments:
            passport_id -- string representing friend's passport ID
        """
        if self.friends.has_key(passport_id):
            return self.friends[passport_id]
        else:
            return None

    def get_friends(self):
        """Return all friends in this group"""
        return self.friends.values()

    def get_online_friends(self):
        """Return all online friends in this group"""
        return filter(lambda f: f.state != States.OFFLINE, self.friends)

class Friend:
    """A friend in the friend list"""
    def __init__(self, passport_id, display_name,
        state = States.OFFLINE, groups = None):

        self.passport_id = passport_id
        self.display_name = display_name
        self.state = state
        self.groups = {}

        if groups == None:
            groups = ()
        for g in groups:
            self.add_to_group(g)

    def get_passport_id(self):
        """Return friend's passport ID"""
        return self.passport_id

    def get_display_name(self):
        """Return friend's display name"""
        return self.display_name

    def get_state(self):
        """Return friend's presence state"""
        return self.state

    def get_groups(self):
        """Return msnp.Group instances representing friend's groups"""
        return self.groups.values()

    def add_to_group(self, group):
        """Add friend to given group"""
        group.friends[self.passport_id] = self
        self.groups[group.id] = group

    def remove_from_group(self, group):
        """Remove friend from given group"""
        del group.friends[self.passport_id]
        del self.groups[group.id]

class FriendList:
    """Friend list
    
    Includes groups, all types of lists (forward, reverse, allow, block), and
    some other book-keeping information.  msnp.Session.friend_list is an
    instance of this class.
    """
    def __init__(self):
        self.ver = 0
        self.groups = {}
        self.lists = {
            Lists.FORWARD: {},
            Lists.REVERSE: {},
            Lists.ALLOW: {},
            Lists.BLOCK: {},
        }
        self.privacy_mode = PrivacyModes.BLOCK
        self.notify_on_add_ = True
        self.dirty = True
        self.updated = time()
        self.temp_iln = {}

    def is_dirty(self):
        """If this list is dirty (needs update from server)"""
        return self.dirty

    def get_group(self, id):
        """Return msnp.Group instance corresponding to the given group ID"""
        if self.groups.has_key(id):
            return self.groups[id]
        else:
            return None

    def get_groups(self):
        """Return all groups in this list"""
        return self.groups.values()

    def get_friend(self, passport_id, list_ = Lists.FORWARD):
        """Return msnp.Friend instance for given passport ID and list type"""
        if self.lists[list_].has_key(passport_id):
            return self.lists[list_][passport_id]
        else:
            return None

    def get_friends(self, list_ = Lists.FORWARD):
        """Return all friends from given list type"""
        return self.lists[list_].values()

    def size(list_):
        """Return size (no. of members) of given list"""
        return len(self.lists[list_])

    def get_online_friends(self):
        """Return all online friends from forward list"""
        return filter(lambda f: f.state != States.OFFLINE,
            self.lists[Lists.FORWARD])

    def get_privacy_mode(self):
        """Return privacy mode (see msnp.PrivacyModes)"""
        return self.privacy_mode

    def notify_on_add(self):
        """Whether or not to be notified on being added to someone's list"""
        return self.notify_on_add_

    def last_updated(self):
        """Last updated timestamp, in seconds since the epoch"""
        return self.updated

# vim: set ts=4 sw=4 et tw=79 :

