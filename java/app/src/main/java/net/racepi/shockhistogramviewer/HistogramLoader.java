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

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class HistogramLoader {

    private final List<BarChart> charts;
    private final List<int[]> renderData = new ArrayList<>(4);
    private int[] xAxis = new int[1];

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
        renderData.add(0, new int[1]);
        renderData.add(1, new int[1]);
        renderData.add(2, new int[1]);
        renderData.add(3, new int[1]);
    }

    /**
     * Set data to be rendered
     *
     * @param jsonData input data from logger as a JSON string
     * @throws JSONException
     */
    public void setData(final String jsonData) throws JSONException {
        final List<JSONArray> jsonArrays = new ArrayList<>();
        final JSONObject root = new JSONObject(jsonData);
        System.out.println("name: " + root.getString("name"));
        jsonArrays.add(root.getJSONArray("LF"));
        jsonArrays.add(root.getJSONArray("RF"));
        jsonArrays.add(root.getJSONArray("LR"));
        jsonArrays.add(root.getJSONArray("RR"));

        xAxis = new int[root.getJSONArray("x_axis").length()];
        for (int j = 0; j <xAxis.length; j++) {
            xAxis[j] = (root.getJSONArray("x_axis").getInt(j));
        }

        if (jsonArrays.size() == charts.size()) {
            for (int i = 0; i < charts.size(); i++) {
                int[] tempData = new int[jsonArrays.get(i).length()];
                for (int j = 0; j < jsonArrays.get(i).length(); j++) {
                    tempData[j] = (jsonArrays.get(i).getInt(j));
                }
                renderData.add(i, tempData);
            }
        }
    }

    /**
     * Load bar data into plots and render. This must be called from the UI thread.
     */
    public void loadData() {
        for (int corner = 0; corner < charts.size(); corner++) {
            final BarChart chart = charts.get(corner);
            final int[] data = renderData.get(corner);
            final List<BarEntry> entries = new ArrayList<>();
            for (int i = 0 ; i < data.length ; i++) {
                entries.add(new BarEntry(xAxis[i], data[i]));
            }
            final BarDataSet dataSet = new BarDataSet(entries, null);
            dataSet.setColors(ColorTemplate.COLORFUL_COLORS);
            final BarData barData = new BarData(dataSet);
            barData.setBarWidth((xAxis[xAxis.length-1] - xAxis[0]) / xAxis.length);
            chart.setData(barData);
            chart.invalidate();
        }
    }
}
