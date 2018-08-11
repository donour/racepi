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

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.Intent;
import android.support.annotation.NonNull;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.Spinner;
import android.widget.TextView;

import com.github.mikephil.charting.charts.BarChart;

import org.json.JSONException;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.UUID;

public class MainActivity extends AppCompatActivity {
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    private final static int REQUEST_ENABLE_BT = 1;
    private HistogramLoader histogramLoader;

    private class ConnectedThread extends Thread {

        private final BluetoothDevice device;

        ConnectedThread(final BluetoothDevice device) {
            this.device = device;
        }

        public void run() {
            try (final BluetoothSocket socket =
                         device.createRfcommSocketToServiceRecord(SPP_UUID)) {
                socket.connect();
                final BufferedWriter writer = new BufferedWriter(
                        new OutputStreamWriter(socket.getOutputStream(),
                                Charset.forName("ascii")));
                final InputStream is = socket.getInputStream();
                writer.write("histogram");
                writer.flush();
                while (is.available() <= 0) {
                    try {
                        sleep(10);
                    } catch (final InterruptedException e) {
                        e.printStackTrace();
                    }
                }
                // read all available
                final StringBuilder sb = new StringBuilder();
                while (is.available() > 0) {
                    sb.append((char) is.read());
                }
                final String result = sb.toString();
                histogramLoader.setData(new HistogramData(result));
            } catch (final IOException | JSONException e) {
                e.printStackTrace();
            } finally {
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        histogramLoader.loadData();
                        final Button loadButton = findViewById(R.id.loadButton);
                        loadButton.setEnabled(true);
                    }
                });
            }
        }
    }

    @Override
    protected void onCreate(final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        final List<BarChart> charts = new ArrayList<BarChart>();
        charts.add((BarChart) findViewById(R.id.lf_chart));
        charts.add((BarChart) findViewById(R.id.rf_chart));
        charts.add((BarChart) findViewById(R.id.lr_chart));
        charts.add((BarChart) findViewById(R.id.rr_chart));
        final List<TextView> currentPositionTextViews = new ArrayList<>();
        currentPositionTextViews.add((TextView) findViewById(R.id.positionTextViewLF));
        currentPositionTextViews.add((TextView) findViewById(R.id.positionTextViewRF));
        currentPositionTextViews.add((TextView) findViewById(R.id.positionTextViewLR));
        currentPositionTextViews.add((TextView) findViewById(R.id.positionTextViewRR));

        histogramLoader = new HistogramLoader(charts, currentPositionTextViews);

        final BluetoothAdapter bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (bluetoothAdapter == null) {
            // TODO bluetooth not supported
        }
        if (!bluetoothAdapter.isEnabled()) {
            // query user for enabling bl
            Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
            startActivityForResult(enableBtIntent, REQUEST_ENABLE_BT);
        }

        final Set<BluetoothDevice> bondedDevices = bluetoothAdapter.getBondedDevices();
        final Spinner bondedDevicesSpinner = findViewById(R.id.bondedDevicesSpinner);
        // Creating adapter for spinner
        final ArrayAdapter<BluetoothDevice> dataAdapter =
                new ArrayAdapter<BluetoothDevice>(this,
                        android.R.layout.simple_spinner_item, new ArrayList<>(bondedDevices))
        {
            @NonNull
            @Override
            public View getView(int position, View convertView, @NonNull ViewGroup parent) {
                final TextView view = (TextView) super.getView(position, convertView, parent);
                // Replace text with my own
                final BluetoothDevice device = getItem(position);
                if (device == null) {
                    view.setText("[unknown device]");
                } else {
                    view.setText(String.format("%s (%s)", device.getName(), device.getAddress()));
                }
                return view;
            }
            @Override
            public View getDropDownView(int position, View convertView, @NonNull ViewGroup parent) {
                return getView(position, convertView, parent);
            }
        };
        dataAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        bondedDevicesSpinner.setAdapter(dataAdapter);

        final Button loadButton = findViewById(R.id.loadButton);
        loadButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(final View view) {
                loadButton.setEnabled(false);
                final BluetoothDevice device =
                        (BluetoothDevice) bondedDevicesSpinner.getSelectedItem();
                final ConnectedThread thr = new ConnectedThread(device);
                thr.start();
            }
        });
    }
}
