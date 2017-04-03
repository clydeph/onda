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


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy
from scipy import ndimage

import cfelpyutils.cfel_hdf5 as ch5


######################
# DARKCAL CORRECTION #
######################

class DarkCalCorrection:
    """DarkCal correction

    Implements DarkCal correction. Applies DarkCal correction to
    data, by simple subtraction. Optionally, a gain map can be also applied.
    """

    def __init__(self, filename, hdf5_group, apply_mask=False,
                 mask_filename=None, mask_hdf5_group=False,
                 gain_map_correction=False, gain_map_filename=None,
                 gain_map_hdf5_group=None):
        """Initializes the DarkCal correction algorithm.

        Args:

            filename (str): name of the hdf5 5 with dark calibration data

            hdf5_group (str): path of the dark calibration data within the hdf5 file.

            apply_mask (Optional[bool]): whether a mask should be applied (optional, if omitted no mask is applied).

            mask_filename (Optional[str]) : if the mask is applied, name of the hdf5 file with gain_map, otherwise
            ignored. This argument must be only be provided if the apply_mask argument is set to True.

            mask_hdf5_group (Optional[str]): if the mask is applied, internal hdf5 path of the data block containing
            the mask, otherwise ignored. This argument must be only be provided if the apply_mask argument is set to
            True.

            gain_map_correction (Optional[bool]): whether a gain_map should be applied. This is optional, and if
            omitted no gain map is applied.

            gain_map_filename (Optional[str]): if the gain map is applied, name of the hdf5 file with gain_map,
            otherwise ignored (optional). This argument must be only be provided if the gain_map_correction
            argument is set to True.

            gain_map_hdf5_group (Optional[str]): if the gain map is applied, internal hdf5 path of the data block
            containing the mask, otherwise ignored (optional). This argument must be only be provided if the
            gain_map_correction argument is set to True.
         """

        # load the darkcals
        self.darkcal = ch5.load_nparray_from_hdf5_file(filename, hdf5_group)

        if apply_mask:
            self.mask = ch5.load_nparray_from_hdf5_file(mask_filename,
                                                        mask_hdf5_group)
        else:
            self.mask = True

        if gain_map_correction:
            self.gain_map = ch5.load_nparray_from_hdf5_file(gain_map_filename, gain_map_hdf5_group)
        else:
            self.gain_map = True

    def apply_darkcal_correction(self, data_as_slab):
        """Applies the correction.

        Args:

            data_as_slab (numpy.ndarray): the data on which to apply the DarkCal correction, in 'slab' format.
        """

        return (data_as_slab * self.mask - self.darkcal) * self.gain_map


#########################
# SIMPLE PEAK DETECTION #
#########################

class SimplePeakDetection:
    """Peak finding using a simple threshold-based algorithm.

    Implements a simple threshold-based peak finding algorithm. The algorithm finds peaks by thresholding the input
    data, identifying 'islands' of pixels with values above the threshold, and using as peak location the center of
    mass of the 'islands' (computed with a window of predefined size).
    """

    def __init__(self, threshold, window_size):
        """Initializes the peakfinder.

        Args:

            threshold (float): threshold for peak detection.

            window_size (int): edge size of the window used to determine the center of mass of each peak (the window
            is centered around the pixel with highest intensity).
        """

        self.threshold = threshold
        self.peak_window_size = window_size
        self.neighborhood = ndimage.morphology.generate_binary_structure(2, 5)

    def find_peaks(self, raw_data):
        """Finds peaks.

        Performs the peak finding.

        Designed to be run on worker nodes.

        Args:

            raw_data (numpy.ndarray): the data on which peak finding is performed, in 'slab' format.

        Returns:

            peak_list (tuple):  the peak list, as a tuple of three

            lists: ([peak_x], [peak_y], [peak_value]). The first two contain the coordinates of the peaks in the
            input data array, the third the intensity of the peaks. All are lists of float numbers.
        """

        local_max = ndimage.filters.maximum_filter(
            raw_data, footprint=self.neighborhood)
        data_as_slab_peak = (raw_data == local_max)
        data_as_slab_thresh = (raw_data > self.threshold)
        data_as_slab_peak[data_as_slab_thresh == 0] = 0
        peak_list = numpy.where(data_as_slab_peak == 1)
        peak_values = raw_data[peak_list]

        if len(peak_list[0]) > 10000:
            print('Silly number of peaks {0}'.format(len(peak_list[0])))
            peak_list = ([], [], [])
        elif len(peak_list[0]) != 0:
            subpixel_x = []
            subpixel_y = []
            for x_peak, y_peak in zip(peak_list[0], peak_list[1]):
                peak_window = raw_data[x_peak - self.peak_window_size:x_peak + self.peak_window_size + 1,
                                       y_peak - self.peak_window_size:y_peak + self.peak_window_size + 1]
                if peak_window.shape[0] != 0 and peak_window.shape[1] != 0:
                    offset = scipy.ndimage.measurements.center_of_mass(peak_window)
                    offset_x = offset[0] - self.peak_window_size
                    offset_y = offset[1] - self.peak_window_size
                    subpixel_x.append(x_peak + offset_x)
                    subpixel_y.append(y_peak + offset_y)
                else:
                    subpixel_x.append(x_peak)
                    subpixel_y.append(y_peak)

            peak_list = (subpixel_x, subpixel_y, peak_values)
        else:
            peak_list = ([], [], [])

        return peak_list


####################
# PEAK ACCUMULATOR #
####################

class PeakAccumulator:
    """Accumulates found peaks

    Accumulates peaks provided by the user until a predefinel number of additions have been reached, then it returns the
    full list of accumulated peaks.
    """

    def __init__(self, accumulated_shots):
        """Initializes the accumulator

        Args:

                accumulated_shots(int): the number of peak additions to accumulate before returning the peak list
        """

        self.accumulated_shots = accumulated_shots
        self.accumulator = ([], [], [])
        self.events_in_accumulator = 0

    def accumulate_peaks(self, peak_list):
        """Accumulates peaks.

        Accumulates peaks. The peaks are added to an internal list of peaks. When peaks have been added to the list for
        a numer of times specified by the accumulated_shots algorithm parameter, the function returns the accumulated
        peak list to the user and empties it.

        Designed to be run on the master node.

        Args:

            peak_list (tuple): list of peaks to be added to the internal list. The peak list should be a tuple of
            three lists, containing, in order, the fs coordinate of the peaks, their respective ss coordinate , and
            their intensity.

        Returns:

            peak_list (tuple or None):  the accumulated peak_list if peaks have been added to the list for the number
            of times specified by the accumulated_shots parameter, None otherwise. If returned, the peak list is a tuple
            of three lists, containing, in order, the fs coordinate of the peaks, their respective ss coordinate , and
            their intensity.
        """

        self.accumulator[0].extend(peak_list[0])
        self.accumulator[1].extend(peak_list[1])
        self.accumulator[2].extend(peak_list[2])
        self.events_in_accumulator += 1

        if self.events_in_accumulator == self.accumulated_shots:
            peak_list_to_return = self.accumulator
            self.accumulator = ([], [], [])
            self.events_in_accumulator = 0
            return peak_list_to_return
        return None


######################
# RAW DATA AVERAGING #
######################

class RawDataAveraging:
    """Averages raw data.

    Accumulates raw data images and returns the average image when the required number of shots have been collected.
    """

    def __init__(self, accumulated_shots, slab_shape):
        """Initializes the raw data averaging algorithm.

        Args:

            accumulated_shots (int): the number images to accumulate before returning the average image.

            slab_shape (tuple): shape of the numpy.ndarray containing the data to be accumulated.
        """

        self.accumulated_shots = accumulated_shots

        self.slab_shape = slab_shape
        self.num_raw_data = 0
        self.avg_raw_data = numpy.zeros(slab_shape)

    def accumulate_raw_data(self, data_as_slab):
        """Accumulates peaks.

        Accumulates raw data images. When the number of images specified specified by the accumulated_shots class
        attribute is reached, the function returns the average image.

        Args:

            data_as_slab (numpy.ndarray): raw data image to add, in 'slab' format.

        Returns:

            avg_raw_data (tuple or None):  the average image if the number of images specified by the accumulated_shots
            class attribute has been reached, None otherwise.
        """

        if self.num_raw_data == self.accumulated_shots:
            self.num_raw_data = 0
            self.avg_raw_data.fill(0)

        self.avg_raw_data += (data_as_slab / self.accumulated_shots)
        self.num_raw_data += 1
        if self.num_raw_data == self.accumulated_shots:
            return self.avg_raw_data
        return None


########################
# OPTICAL LASER STATUS #
########################

class OpticalLaserStatus:
    """Informs about optical laser status (ON or OFF).

    Provides information about the optical laser status (ON or OFF) by inspecting the event codes for the event.
    """

    def __init__(self, role, laser_on_event_codes):
        """Initializes the optical laser status algorithm.

        Args:

            laser on event codes (tuple): tuple containing the event codes (as ints) that correspond to the optical
            laser being on. The optical laser is assumed to be on only if all event codes in the tuple are present in
            the list of event codes for a specific event.

            If the list of laser on event codes is set to None, the laser is reported as being always off.
        """

        self.laser_on_event_codes = laser_on_event_codes


    def is_optical_laser_on(self, event_codes):
        """Reports if optical laser is on.

        Inspects the provided event codes and reports if the optical laser is on.

        Designed to be run on the worker node.

        Args:

            data_as_slab (numpy.ndarray): raw data image to add, in 'slab' format.

        Returns:

            avg_raw_data (tuple or None):  the average image if the number of images specified by the accumulated_shots
            class attribute has been reached, None otherwise.
        """

        try:
            return all(x in event_codes for x in self.laser_on_event_codes)
        except:
            return False
