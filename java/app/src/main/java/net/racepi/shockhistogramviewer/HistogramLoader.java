/*
    Copyright 2018 Donour Sizemore

    This file is part of RacePi

    RacePi is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 2.

    RacePi is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with RacePi.  If not, see <http://www.gnu.org/licenses/>.
*/
package net.racepi.shockhistogramviewer;

import com.github.mikephil.charting.charts.BarChart;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.data.BarData;
import com.github.mikephil.charting.data.BarDataSet;
import com.github.mikephil.charting.data.BarEntry;
import com.github.mikephil.charting.utils.ColorTemplate;

import java.util.ArrayList;
import java.util.List;

public class HistogramLoader {

    private final List<BarChart> charts;

    HistogramLoader(final List<BarChart> charts) {
        this.charts = charts;
        for (final BarChart chart : charts) {
            chart.setDragEnabled(false);
            chart.setPinchZoom(false);
            chart.setClickable(false);
            chart.setDoubleTapToZoomEnabled(false);

            chart.setDescription(null);
            chart.getLegend().setEnabled(false);
            chart.getAxisRight().setEnabled(false);

            final XAxis xAxis = chart.getXAxis();
            xAxis.setPosition(XAxis.XAxisPosition.BOTTOM_INSIDE);
            xAxis.setDrawGridLines(false);
        }
    }

    public void loadData() {

        final int[] testData = {
          1,1,1,1,1,4,11,20,40,20,12,4,1,1,1,1,1
        };

        for (final BarChart chart : charts) {

            final List<BarEntry> entries = new ArrayList<>();
            for (int i = (-testData.length/2) ; i <= testData.length/2; i++) {
                entries.add(new BarEntry(i, testData[i+testData.length/2]));
            }
            final BarDataSet dataSet = new BarDataSet(entries, null);
            dataSet.setColors(ColorTemplate.COLORFUL_COLORS);
            chart.setData(new BarData(dataSet));
            chart.invalidate();
        }
    }
}
