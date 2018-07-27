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

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;

import com.github.mikephil.charting.charts.BarChart;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private HistogramLoader histogramLoader;

    @Override
    protected void onCreate(final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        final List<BarChart> charts = new ArrayList<BarChart>();
        charts.add((BarChart) findViewById(R.id.lf_chart));
        charts.add((BarChart) findViewById(R.id.rf_chart));
        charts.add((BarChart) findViewById(R.id.lr_chart));
        charts.add((BarChart) findViewById(R.id.rr_chart));
        histogramLoader = new HistogramLoader(charts);
        histogramLoader.loadData();
    }
}
