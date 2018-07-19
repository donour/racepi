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
#include <string.h>
#include "lwip/sys.h"
#include "lwip/netdb.h"
#include "lwip/api.h"
#include "web_ctrl.h"
#include "shock_sampler.h"

/* 
It's quite absurd that this has to be inplemented on such a low level. There should be 
a simple HTTP request handling library available, but it looks like none is. nghttp doesn't
do HTTP/1. 
*/

const static char HEADER[] = "HTTP/1.1 200 OK\r\nContent-type: text/html; charset=ISO-8859-4 \r\n\r\n";
const static char HTML_HEADER[] ="<html><head><style>table, th, td {border: 1px solid black;}</style><head>";

// TODO the zero button needs to be implemented
const static char HTML_FOOTER[] =
"  <body><div id=\"hist_chart\" style=\"width:100vw; height:90vh;\"></div>"
"  </body></html>";


// must be called inside header processing
static void write_google_charts(struct netconn *conn) {

  static char SCRIPT_HEADER[] =
    "    <script type=\"text/javascript\" src=\"https://www.gstatic.com/charts/loader.js\"></script>"
    "    <script type=\"text/javascript\">"
    "      google.charts.load('current', {'packages':['bar']});"
    "      google.charts.setOnLoadCallback(drawChart);"
    "      function drawChart() {"
    "        var data = google.visualization.arrayToDataTable("
    "        [";
  static char SCRIPT_FOOTER[] = 
    "  ]);"
    "        var options = {chart: {title: 'Histogram'}};"
    "        var chart = new google.charts.Bar(document.getElementById('hist_chart'));"
    "        chart.draw(data, google.charts.Bar.convertOptions(options));"
    "      }</script>";
  
  netconn_write(conn, SCRIPT_HEADER, sizeof(SCRIPT_HEADER)-1, NETCONN_NOCOPY);
  // Legend row
  netconn_write(conn, "['Speed'", 8, NETCONN_NOCOPY);
  for (int column = 0; column < CONFIG_NUM_HISTOGRAM_BUCKETS; column++) {
    char buf[32];
    // TODO populate actual values
    short bucket_val = HISTOGRAM_BUCKET_SIZE*(column - (CONFIG_NUM_HISTOGRAM_BUCKETS)/2); 
    snprintf(buf, 12, ",'%d'", bucket_val);
    netconn_write(conn, buf, strlen(buf), NETCONN_NOCOPY);
  }
  netconn_write(conn, "],", 2, NETCONN_NOCOPY);

  // Write a row for each corner
  for (int corner = 0; corner < CORNER_COUNT; corner++) {
    // write HEADER
    char *header="['unknown'";
    switch(corner) {
        case 0:
	  header="['LF'";
	  break;
        case 1:
	  header="['RF'";
	  break;
        case 2:
	  header="['LR'";
	  break;
        case 3: 
	  header="['RR'";
	  break;
        default:break;
    }
    netconn_write(conn, header, strlen(header), NETCONN_NOCOPY);
    for(int col = 0; col < CONFIG_NUM_HISTOGRAM_BUCKETS; col++) {
      char buf[16];
      sprintf(buf, ",%d", (int)normalized_histogram[corner][col]);
      netconn_write(conn, buf, strlen(buf), NETCONN_NOCOPY);
    }
    netconn_write(conn, "],", 2, NETCONN_NOCOPY);
  }
    netconn_write(conn, SCRIPT_FOOTER, sizeof(SCRIPT_FOOTER)-1, NETCONN_NOCOPY);
}

// must be written in body
static void write_hist_table(struct netconn *conn) {
  netconn_write(conn,"<table>", 7, NETCONN_NOCOPY);
  netconn_write(conn,"<tfoot><tr><th></th>", 20, NETCONN_NOCOPY);  
  for (int column = 0; column < CONFIG_NUM_HISTOGRAM_BUCKETS; column++) {
    char buf[32];
    short bucket_val = HISTOGRAM_BUCKET_SIZE*(column - (CONFIG_NUM_HISTOGRAM_BUCKETS)/2); 
    snprintf(buf, 31, "<th>%d</th>", bucket_val);
    netconn_write(conn, buf, strlen(buf), NETCONN_NOCOPY);
  }
  netconn_write(conn,"</tr></tfoot>", 13, NETCONN_NOCOPY);  

  for (int corner = 0; corner < CORNER_COUNT; corner++) {
    netconn_write(conn,"<tr>", 4, NETCONN_NOCOPY);  
    // write HEADER
    char *header="<td>unknown</td>";
    switch(corner) {
        case 0:
	  header="<TD>LF</TD>";
	  break;
        case 1:
	  header="<TD>RF</TD>";
	  break;
        case 2:
	  header="<TD>LR</TD>";
	  break;
        case 3: 
	  header="<TD>RR</TD>";
	  break;
        default:break;
    }
    netconn_write(conn, header, strlen(header), NETCONN_NOCOPY);
    for(int col = 0; col < CONFIG_NUM_HISTOGRAM_BUCKETS; col++) {
      char buf[32];
      sprintf(buf, "<td>% 2d</td>", (int)normalized_histogram[corner][col]);  
      netconn_write(conn, buf, strlen(buf), NETCONN_NOCOPY);
    }
    netconn_write(conn,"</tr>", 5, NETCONN_NOCOPY);  
  }
  netconn_write(conn,"</table>", 8, NETCONN_NOCOPY);

  netconn_write(conn,"<BR><BR>Recording: ", 19, NETCONN_NOCOPY);
  if (recording_active) {
    netconn_write(conn,"<label>on</label>", 17, NETCONN_NOCOPY);
  } else {
    netconn_write(conn,"<label>off</label>", 18, NETCONN_NOCOPY);
  }
}

static void write_calibration_controls(struct netconn *conn){
  char ctrls[] = "<br><br>"
    "<form action=\"/zero\">"
    "<input type=\"submit\" value=\"Zero Histogram\" />"
    "</form>";
    
  netconn_write(conn, ctrls, strlen(ctrls), NETCONN_NOCOPY);      
}

static void write_page(struct netconn *conn) {
  netconn_write(conn, HEADER, sizeof(HEADER)-1, NETCONN_NOCOPY);
  netconn_write(conn, HTML_HEADER, sizeof(HTML_HEADER)-1, NETCONN_NOCOPY);
  //write_google_charts(conn);
  write_hist_table(conn);
  //write_calibration_controls(conn);
  netconn_write(conn, HTML_FOOTER, sizeof(HTML_FOOTER)-1, NETCONN_NOCOPY);
};

static void handle_zero_request(struct netconn *conn) {
  static char ZERO_RESPONSE[] =
    "HTTP/1.1 301 See Other \nLocation: /";
    /*
    "<html><head>"
    "<meta http-equiv=\"refresh\" content=\"1; URL=/\">"
    "<meta name=\"keywords\" content=automatic redirection>"
    "</head><body></body></html>";
    netconn_write(conn, HEADER, sizeof(HEADER)-1, NETCONN_NOCOPY);
    */

  netconn_write(conn, ZERO_RESPONSE, sizeof(ZERO_RESPONSE), NETCONN_NOCOPY);
}

static void handle_request(struct netconn *conn)
{
  char *buf;
  u16_t buflen;
  err_t err;
  struct netbuf *rx_buffer;

  // TODO: allow for multi part requests
  err = netconn_recv(conn, &rx_buffer);
  if (ERR_OK == err) {
    netbuf_data(rx_buffer, (void**)&buf, &buflen);
    if ( ! strncmp("GET", buf, 3)) {

      if (strstr(buf, "/zero") != NULL) {
	//zero_histogram();
	//printf("zeroed\n");
	//handle_zero_request(conn);
      } else {
	populate_normalized_histogram();
	write_page(conn);
      }
    } else {
      printf("unknown request: %s\n", buf);
    }
  }
  netbuf_delete(rx_buffer);
}

/*
 * Task to accept incoming connections
 */
void httpd_task(void *parameters_unused)
{
  struct netconn *conn;
  struct netconn *newconn;
  err_t err;
  
  conn = netconn_new(NETCONN_TCP);
  netconn_bind(conn, NULL, CONFIG_WEB_SERVER_PORT);
  netconn_listen(conn);
  do {
     err = netconn_accept(conn, &newconn);
     if (err == ERR_OK) {
       handle_request(newconn);
       netconn_close(newconn);
       netconn_delete(newconn);
     }
   } while(err == ERR_OK);
   netconn_close(conn);
   netconn_delete(conn);
}
