# This file is part of OnDA.
#
# OnDA is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# OnDA is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with OnDA.
# If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2014-2018 Deutsches Elektronen-Synchrotron DESY,
# a research centre of the Helmholtz Association.
"""
Event structure.

Structure used to store retrieved events.
"""
from __future__ import absolute_import, division, print_function

import types

from future.utils import iteritems


class DataEvent(object):
    """
    Retrieved event information and data.

    Stores data and information for an event retrieved from a facility. Event handling
    methods, used to open, close and get basic information about the event, are
    defined when an instance of the class is created. Data extraction functions are
    instead injected dynamically, based on users' requests, after the creation of the
    class.
    """

    def __init__(self, open_event_func, close_event_func, get_num_frames_in_event_func):
        """
        Initializes the Event class.

        Args:

            open_event_func (function): function used to open the event and make
                available the data contained therein for further processing.

            close_event_func (function): function used to close the event before
                getting ready to to the next one.

            get_num_frames_in_event (function): function used to determine how many
                frames the event contain.
        """

        self.open_event = types.MethodType(open_event_func, self)
        self.close_event = types.MethodType(close_event_func, self)
        self.get_num_frames_in_event = types.MethodType(
            get_num_frames_in_event_func, self
        )

        self.data = None
        self.metadata = None
        self.timestamp = None
        self.current_frame = None
        self.framework_info = {}
        self.data_extraction_functions = {}

    def extract_data(self):
        """
        Extracts data from event.

        Runs the necessary data extraction functions and returns a dictionary where
        the keys are the name of the data extraction functions and the values are
        the results returned by each function.
        """
        data = {}
        for f_name, func in iteritems(self.data_extraction_functions):
            print("Error extracting {0}.".format(func.__name__))
            data[f_name] = func(self)

        print('Data:', data.keys())
        return data
