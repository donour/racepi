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

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class HistogramData {
    private final int[] currentPositions;
    private final List<int[]> cornerData = new ArrayList<>();
    private final int[] xAxis ;

    public HistogramData(final String jsonData) throws JSONException {
        final List<JSONArray> jsonArrays = new ArrayList<>();
        final JSONObject root = new JSONObject(jsonData);
        jsonArrays.add(root.getJSONArray("LF"));
        jsonArrays.add(root.getJSONArray("RF"));
        jsonArrays.add(root.getJSONArray("LR"));
        jsonArrays.add(root.getJSONArray("RR"));

        if (root.has("x_axis")) {
            xAxis = new int[root.getJSONArray("x_axis").length()];
            for (int j = 0; j < xAxis.length; j++) {
                xAxis[j] = (root.getJSONArray("x_axis").getInt(j));
            }
        } else {
            throw new JSONException("missing x_axis field");
        }

        for (int i = 0; i < jsonArrays.size(); i++) {
            int[] tempData = new int[jsonArrays.get(i).length()];
            for (int j = 0; j < jsonArrays.get(i).length(); j++) {
                tempData[j] = (jsonArrays.get(i).getInt(j));
            }
            cornerData.add(i, tempData);
        }

        if (root.has("current_positions_mm")) {
            currentPositions = new int[root.getJSONArray("current_positions_mm").length()];
            for (int j = 0; j < currentPositions.length; j++) {
                currentPositions[j] = (root.getJSONArray("current_positions_mm").getInt(j));
            }
        } else {
            currentPositions = null;
        }
    }

    public List<int[]> getCornerData() {
        return cornerData;
    }

    public int[] getxAxis() {
        return xAxis;
    }

    public int[] getCurrentPositions() {
        return currentPositions;
    }
}
