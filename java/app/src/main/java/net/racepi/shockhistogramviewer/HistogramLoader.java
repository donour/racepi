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

import android.widget.TextView;

import com.github.mikephil.charting.charts.BarChart;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.data.BarData;
import com.github.mikephil.charting.data.BarDataSet;
import com.github.mikephil.charting.data.BarEntry;
import com.github.mikephil.charting.utils.ColorTemplate;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.List;

public class HistogramLoader {

    private final List<BarChart> charts;
    private final List<TextView> currentPositionTextViews;
    private HistogramData data = null;

    HistogramLoader(final List<BarChart> charts, final List<TextView> currentPositionTextViews) {
        this.charts = charts;
        this.currentPositionTextViews = currentPositionTextViews;
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

    public void setData(final HistogramData data) {
        this.data = data;
    }

    /**
     * Load bar data into plots and render. This must be called from the UI thread.
     */
    public void loadData() {
        if (data.getCornerData().size() < charts.size()){
            return;
        }

        for (int corner = 0; corner < charts.size(); corner++) {
            final BarChart chart = charts.get(corner);
            final int[] cornerData = data.getCornerData().get(corner);
            loadDataIntoChart(chart, cornerData, data.getxAxis());
        }
        if (data.getCurrentPositions() != null &&
                data.getCurrentPositions().length == currentPositionTextViews.size())
        {
            for(int i = 0; i < data.getCurrentPositions().length; i++) {
                currentPositionTextViews.get(i).setText(
                        String.format("%3d",
                                data.getCurrentPositions()[i], Charset.defaultCharset()));
            }
        }
    }

    private void loadDataIntoChart(final BarChart chart, final int[] chartData, final int[] xAxis) {
        final List<BarEntry> entries = new ArrayList<>();
        for (int i = 0 ; i < chartData.length ; i++) {
            entries.add(new BarEntry(data.getxAxis()[i], chartData[i]));
        }
        final BarDataSet dataSet = new BarDataSet(entries, null);
        dataSet.setColors(ColorTemplate.COLORFUL_COLORS);
        final BarData barData = new BarData(dataSet);
        barData.setBarWidth((data.getxAxis()[data.getxAxis().length-1] - data.getxAxis()[0]) / data.getxAxis().length);
        chart.setData(barData);
        chart.invalidate();

    }
}
