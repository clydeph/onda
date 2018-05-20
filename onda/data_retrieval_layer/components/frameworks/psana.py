#    This file is part of OnDA.
#
#    OnDA is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OnDA is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with OnDA.  If not, see <http://www.gnu.org/licenses/>.
"""
Functions and classes to recover and process data from HiDRA.

Exports:

    Functions:

        initialize_event_source: connect to the event source and
            configure it.

        event_generator: event recovery from HiDRA.

    Classes:

        EventFilter (class): filter and reject events.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
from builtins import str  # pylint: disable=W0622

import numpy
from future.utils import iteritems

import psana  # pylint: disable=E0401
from onda.utils import dynamic_import


def _psana_offline_event_generator(psana_source,
                                   node_rank,
                                   mpi_pool_size):
    for run in psana_source.runs():
        times = run.times()
        size_for_this = int(
            numpy.ceil(
                len(times) / float(mpi_pool_size - 1)
            )
        )
        events_for_this = times[
            (node_rank - 1) * size_for_this:node_rank * size_for_this
        ]
        for evt in events_for_this:
            yield run.event(evt)


def initialize_event_source(source,  # pylint: disable=W0613
                            node_rank,  # pylint: disable=W0613
                            mpi_pool_size,  # pylint: disable=W0613
                            monitor_params):  # pylint: disable=W0613
    """
    Initialize event generator.

    Connect to the event generator and configure it. Psana does not
    need to be configured, so do nothing.

    Args:

        source (str): the IP or hostname of the machine where hidra is
            running.

        node_rank (int): rank of the node where the function is called

        mpi_pool_size (int): size of the node pool that includes the
            node where the function is called.

        monitor_params (MonitorParams): a MonitorParams object
            containing the monitor parameters from the
            configuration file.
    """
    pass


def event_generator(source,
                    node_rank,
                    mpi_pool_size,  # pylint: disable=W0613
                    monitor_params):
    """
    Initialize psana event recovery.

    Initialize the connection with Psana. Return an iterator which will
    recover an event from psana at each step (This function is a
    python generator).

    Args:

        source (str): the IP or hostname of the machine where hidra is
            running.

        node_rank (int): rank of the node where the function is called

        mpi_pool_size (int): size of the node pool that includes the
            node where the function is called.

        monitor_params (MonitorParams): a MonitorParams object
            containing the monitor parameters from the
            configuration file.

     Yields:

        Dict: A dictionary containing the data and the metadata of a
        retrieved psana event (usually corresponding to a frame).
    """
    if 'shmem' in source:
        offline = False
    else:
        offline = True

    # If the psana calibration directory is provided in the
    # configuration file, add it as an option to psana. Also,
    # automatically add 'idx' to the source string for offline data,
    # if it is not already there.
    psana_calib_dir = monitor_params.get_param(
        section='PsanaDataRecoveryLayer',
        parameter='psana_calibration_directory',
        type_=str
    )
    if psana_calib_dir:
        psana.setOption(
            'psana.calib-dir'.encode('ascii'),
            psana_calib_dir.encode('ascii')
        )

    if offline and not source[-4:] == ':idx':
        source += ':idx'

    # Set the psana data source and recover the psana detector
    # interface initialization functions.
    psana_source = psana.DataSource(source.encode('ascii'))
    psana_interface_funcs = dynamic_import.init_psana_interface_funcs(
        monitor_params
    )

    # Call all the required psana interface functions and store the
    # returned handlers in a dictionary.
    psana_interface = {}
    for f_name, func in iteritems(psana_interface_funcs):
        psana_interface[f_name.split("_init")[0]] = func(monitor_params)

    # Recover the event iterator from the psana DataSource object
    # if running online. Otherwise, split the events based on the
    # number of workers and have each worker iterate only on the events
    # assigned to him.
    if offline:
        psana_events = _psana_offline_event_generator(
            psana_source=psana_source,
            node_rank=node_rank,
            mpi_pool_size=mpi_pool_size
        )
    else:
        psana_events = psana_source.events()

    for psana_event in psana_events:
        # Recover the psana?event from psana. Create the event
        # dictionary and store the psana_event there, together with
        # the psana interface functions. Then yield the event.
        event = {
            'psana_interface': psana_interface,
            'psana_event': psana_event
        }
        yield event


class EventFilter(object):
    """
    Filter events.

    Reject files whose 'age' (the time between the data collection and
    the moment OnDA receives the data) is higher than a predefined
    threshold.
    """
    def __init__(self,
                 monitor_params):
        """
        Initialize the EventFilter class.

        Args:

        monitor_params (MonitorParams): a MonitorParams object
            containing the monitor parameters from the
            configuration file.
        """
        # Read the maximum 'age' threshold from the configuration file
        # and store it in an attribute.
        rejection_threshold = monitor_params.get_param(
            section='PsanaDataRecoveryLayer',
            parameter='event_rejection_threshold',
            type_=float
        )
        if rejection_threshold:
            self._event_rejection_threshold = rejection_threshold
        else:
            self._event_rejection_threshold = 10000000000

    def should_reject(self,
                      event):
        """
        Decide on event rejection.

        Decide if the event should be rejected based on its 'age' (
        the time between data collection and the moment OnDA gets
        the event).

        Args:

            event (Dict): a dictionary with the event data.

        Returns:

            bool: True if the event should be rejected. False if the
            event should be processed.
        """
        # Recover the timestamp from the psana event
        timestamp_epoch_format = event['psana_event'].get(
            psana.EventId  # pylint: disable=E1101
        ).time()

        event_timestamp = numpy.float64(  # pylint: disable=E1101
            str(timestamp_epoch_format[0]) + '.' +
            str(timestamp_epoch_format[1])
        )

        time_now = numpy.float64(time.time())  # pylint: disable=E1101
        if (time_now - event_timestamp) > self._event_rejection_threshold:
            # Store the timestamp in the event dictionary so it does
            # note have to be extracted again if the timestamp is one
            # of the requested data sources.
            return True
        else:
            event['timestamp'] = event_timestamp
            return False


def open_event(event):  # pylint: disable=W0613
    """
    Open event.

    Open the event. Events do not need to be opened in psana, so do
    nothing.

    Args:

        event (Dict): a dictionary with the event data.
    """
    pass


def close_event(event):  # pylint: disable=W0613
    """
    Close event.

    Close the event. Events do not need to be closed in psana, so do
    nothing.

    Args:

        event (Dict): a dictionary with the event data.
    """
    pass


def get_num_frames_in_event(event):  # pylint: disable=W0613
    """
    The number of frames in the file.

    Return the number of frames in a file. In psana an event contains
    just one frame, so return 1.

    Args:

        event (Dict): a dictionary with the event data.
    """
    return 1
