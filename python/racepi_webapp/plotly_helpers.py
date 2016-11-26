# Copyright 2016 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.

from plotly import graph_objs as pgo
from plotly import tools

import pandas as pd


def sfl(float_list, ndigits = 3):
    """
    Shorten a list of float by rounding to a small number of
    decimals. This significantly speeds up loading large datasets
    as JSON
    :param float_list: list of float values
    :param ndigits: number of rounding digits
    :return: list of values round to small number of digits
    """
    return [round(x, ndigits) for x in float_list]


def get_scatterplot(series, w, title, y_axis_id=1):
    """
    Generate plotly scatter plot from pandas timeseries data

    :param series: plot dataframe series
    :param w: rolling averge window radius
    :param title: title for plot
    :return: scatterplot graph object
    """
    xdata = None
    ydata = None
    if len(series) > (2*w):
        data = pd.Series(series).rolling(window=w, center=True).mean()
        t0 = data.index.values.tolist()[0]
        data.offset_time = [x-t0 for x in data.index.values.tolist()]
        xdata = sfl(data.offset_time[w:-w])
        ydata = sfl(data.values.tolist()[w:-w])

    return pgo.Scatter(x=xdata, y=ydata, name=title, yaxis='y'+str(y_axis_id))


def get_xy_combined_plot(sources, title=None):
    if not sources:
        return None

    data = []
    layout = {'title': title,
              'xaxis': dict(
                  title="time",
                  domain=[0.03*len(sources), 1]
              )}

    for i in range(len(sources)):
        s = sources[i]
        data.append(get_scatterplot(s[0], s[1], s[2], i+1))
        axis_name = "yaxis"
        if i > 0:
            axis_name += str(i+1)
            layout[axis_name] = dict(
                title="",
                overlaying='y',
                side='left',
                position=float(0.03 * i)
            )
        else:
            layout[axis_name] = dict(title="")

    fig = pgo.Figure(data=data, layout=layout)
    return fig
