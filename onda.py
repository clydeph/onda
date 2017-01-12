#!/usr/bin/env python
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

from configparser import ConfigParser

import parallelization_layer.utils.onda_params as oa
import cfelpyutils.cfel_optarg as coa
import parallelization_layer.utils.onda_dynamic_import as di
import parallelization_layer.utils.onda_optargs as ooa


if __name__ == "__main__":
    args = ooa.parse_onda_cmdline_args()

    config = ConfigParser()
    config.read(args.ini)

    oa.monitor_params = coa.parse_parameters(config)

    processing_layer = di.import_correct_layer_module('processing_layer', oa.monitor_params)
    Onda = di.import_class_from_layer('Onda', processing_layer)

    mon = Onda(args.source)
    mon.start(verbose=False)
