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
# Copyright 2014-2019 Deutsches Elektronen-Synchrotron DESY,
# a research centre of the Helmholtz Association.
"""
Retrieval of Pilatus detector data from files.

This module contains functions that retrieve data from files written by a Pilatus x-ray
detector.
"""
from __future__ import absolute_import, division, print_function

from typing import Tuple  # pylint: disable=unused-import

import fabio

from onda.utils import data_event, named_tuples  # pylint: disable=unused-import


#####################
#                   #
# UTILITY FUNCTIONS #
#                   #
#####################


def get_file_extensions():
    # type: () -> Tuple[str, ...]
    """
    Retrieves a list of extensions used by Pilatus data files.

    Returns:

        Tuple[str, ...]: the list of file extensions.
    """
    return (".cbf",)


def get_peakfinder8_info():
    # type () -> named_tuples.Peakfinder8Info
    """
    Retrieves the peakfinder8 information for the Pilatus detector.

    Returns:

        :class:`~onda.utils.named_tuples.Peakfinder8Info`: a named tuple storing the
        peakfinder8 information.
    """
    return named_tuples.Peakfinder8Info(
        asic_nx=2463, asic_ny=2527, nasics_x=1, nasics_y=1
    )


def get_hidra_transport_type():
    # type () -> named_tuples.Peakfinder8Info
    """
    Retrieves the HiDRA transport type information for the Pilatus detector.

    Returns:

        str: a string with the data transpor type
    """
    return "data"


############################
#                          #
# EVENT HANDLING FUNCTIONS #
#                          #
############################


def open_event(event):
    # type: (data_event.DataEvent) -> None
    """
    Opens an event retrieved from Pilatus files.

    For Pilatus data files, an event corresponds to the full content of a single
    Pilatus CBF file. This function makes the content of the file available in the
    'data' field of the 'event' object.

    NOTE: This function is designed to be injected as a member function into an
    :class:`~onda.utils.data_event.DataEvent` object.

    Arguments:

        event (:class:`~onda.utils.data_event.DataEvent`): an object storing the event
            data.
    """
    event.data = fabio.open(event.framework_info["full_path"])


def close_event(event):
    # type: (data_event.DataEvent) -> None
    """
    Closes an event retrieved from Pilatus files.

    Since an event corresponds to a CBF data file, which does not need to be closed,
    this function actually does nothing.

    NOTE: This function is designed to be injected as a member function into an
    :class:`~onda.utils.data_event.DataEvent` object.

    Arguments:

        event (:class:`~onda.utils.data_event.DataEvent`): an object storing the event
            data.
    """
    del event


def get_num_frames_in_event(event):
    # type: (data_event.DataEvent) -> int
    """
    Gets the number of frames in an event retrieved from Pilatus files (or HiDRA).

    For the Pilatus detector, an event corresponds to the content of a single CBF data
    file. Since the Pilatus detector writes one frame per file, this function always
    returns 1.

    NOTE: This function is designed to be injected as a member function into an
    :class:`~onda.utils.data_event.DataEvent` object.

    Arguments:

        event (:class:`~onda.utils.data_event.DataEvent`): an object storing the event
            data.

    Returns:

        int: the number of frames in the event.
    """
    del event

    return 1


#############################
#                           #
# DATA EXTRACTION FUNCTIONS #
#                           #
#############################


def detector_data(event):
    # type: (data_event.DataEvent) -> numpy.ndarray
    """
    Retrieves one frame of Pilatus detector data from files (or HiDRA).

    Arguments:

        event (:class:`~onda.utils.data_event.DataEvent`): an object storing the event
            data.

    Returns:

        numpy.ndarray: one frame of detector data.
    """
    # Returns the data from the fabio cbf_obj object previously stored in the event.
    return event.data.data


def event_id(event):
    # type: (data_event.DataEvent) -> str
    """
    Gets a unique identifier for an event retrieved from Pilatus files (or HiDRA).

    Returns a label that unambiguosly identifies, within an experiment, the event
    currently being processed. For the Pilatus detector, an event corresponds to a
    single CBF file, and the full path to the file is used as identifier.

    Arguments:

        event (:class:`~onda.utils.data_event.DataEvent`): an object storing the event
            data.

    Returns:

        str: a unique event identifier.
    """
    return event.framework_info["full_path"]


def frame_id(event):
    # type: (data_event.DataEvent) -> str
    """
    Gets a unique identifier for a Pilatus data frame retrieved from files (or HiDRA).

    Returns a label that unambiguosly identifies, within an event, the frame currently
    being processed. For the Pilatus detector, the index of the frame within the event
    is used as identifier. However, each Pilatus event only contains one frame, so this
    function always returns the string "0".

    Arguments:

        event (:class:`~onda.utils.data_event.DataEvent`): an object storing the event
            data.

    Returns:

        str: a unique frame identifier (within an event).
    """
    del event

    return str(0)
