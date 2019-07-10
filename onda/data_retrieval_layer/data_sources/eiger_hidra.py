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
Retrieval Eiger detector data from HiDRA at Petra III.

Functions used to retrieve, using the HiDRA framework, data from the Eiger detector as
used at the Petra III facility.
"""
from __future__ import absolute_import, division, print_function

import h5py

from onda.utils import named_tuples


#####################
#                   #
# UTILITY FUNCTIONS #
#                   #
#####################


def get_file_extensions():
    """
    Extensions used for Eiger files at Petra III.

    Returns the extensions used for files written by the Eiger detector at the Petra
    III facility.

    Returns:

        Tuple[str]: the list of file extensions.
    """
    return (".nxs", ".h5")


def get_peakfinder8_info():
    """
    Peakfinder8 info for the Eiger detector at Petra III.

    Retrieves the peakfinder8 information matching the data format used by the Eiger
    detector at the Petra III facility.

    Returns:

        Peakfinder8DetInfo: the peakfinder8-related detector information.
    """
    return named_tuples.Peakfinder8DetInfo(
        asic_nx=1556, asic_ny=516, nasics_x=1, nasics_y=1
    )


############################
#                          #
# EVENT HANDLING FUNCTIONS #
#                          #
############################


def open_event(event):
    """
    Opens an Eiger event retrived through Hidra.

    Makes the content of a retrieved Eiger event available in the 'data' entry of the
    event dictionary.

    Args:

        event (Dict): a dictionary with the event data.
    """
    # The event is an HDF5 file. The h5py File function is used to open it.
    event["data"] = h5py.File(name=event["full_path"], mode="r")


def close_event(event):
    """
    Closes an Eiger event retrieved through Hidra.

    Args:

        event (Dict): a dictionary with the event data.
    """
    # The event is an HDF5 file. The h5py Close function is used to close it.
    event["data"].close()


def get_num_frames_in_event(event):
    """
    Number of Eiger frames in  Petra III event.

    Returns the number of Eiger detector frames in an event retrieved at the Petra III
    facility (1 event = 1 file).

    Args:

        event (Dict): a dictionary with the event data.

    Retuns:

        int: the number of frames in the event.
    """
    # The data is stored in a 3-d block. The first axis is the nunmber of frames.
    return event["data"]["/entry/data/data"].shape[0]


#############################
#                           #
# DATA EXTRACTION FUNCTIONS #
#                           #
#############################


def detector_data(event):
    """
    One frame of Eiger detector data at Petra III.

    Extracts one frame of Eiger detector data from an event retrieved at the Petra III
    facility.

    Args:

        event (Dict): a dictionary with the event data.

    Returns:

        ndarray: one frame of detector data.
    """
    return event["data"]["/entry/data/data"][event["frame_offset"]]


def event_id(event):
    """
    Retrieves a unique Eiger event identifier at Petra III.

    Returns a unique label that unambiguosly identifies the current Eiger event within
    an experiment. When using the Eiger detector at the Petra III facility, the full
    path to the file containing the event is used as an identifier.

    Args:

        event (Dict): a dictionary with the event data.

    Returns:

        str: a unique event identifier.
    """
    return event["full_path"]


def frame_id(event):
    """
    Retrieves a unique Eiger frame identifier at Petra III.

    Returns a unique label that unambiguosly identifies the current detector frame
    within the event. When using the Eiger detector at the Petra III facility, the
    index of the frame within the file storing the event is used as idenitifier.

    Args:

        event (Dict): a dictionary with the event data.

    Returns:

        str: a unique frame identifier with the event.
    """
    return str(event["data"]["/entry/data/data"].shape[0] + event["frame_offset"])