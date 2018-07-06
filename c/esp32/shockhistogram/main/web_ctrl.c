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
#include "lwip/sys.h"
#include "lwip/netdb.h"
#include "lwip/api.h"
#include "web_ctrl.h"
#include "shock_sampler.h"

const static char HEADER[] = "HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n";
const static char HTML_HEADER[] =
  "<!DOCTYPE html><html><head>"
  "<style> table, th, td { border: 1px solid black; } </style>"
  "<title>Racepi Shock Histogrammer</title> </head>\n"
  "<body> <h1>Shock histograms forthcoming</h1><BR>\n"
  "<table>";

// TODO the zero button needs to be implemented
const static char HTML_FOOTER[] = "</table><br><br> <button type=\"button\">Zero</button></body></html>\n";

static void handle_request(struct netconn *conn)
{
  char hist_row[16]; // TODO get exact size
  char *buf;
  u16_t buflen;
  err_t err;
  struct netbuf *rx_buffer;

  // TODO: allow for multi part requests
  err = netconn_recv(conn, &rx_buffer);
  if (ERR_OK == err) {
    netbuf_data(rx_buffer, (void**)&buf, &buflen);
    
    if ( ! strncmp("GET", buf, 3)) {

      netconn_write(conn, HEADER, sizeof(HEADER)-1, NETCONN_NOCOPY);
      netconn_write(conn, HTML_HEADER, sizeof(HTML_HEADER)-1, NETCONN_NOCOPY);
      for (int corner = 0 ; corner < CORNER_COUNT ; corner++) {
	netconn_write(conn, "<tr>", 4, NETCONN_NOCOPY);
	for(int col = 0; col < CONFIG_NUM_HISTOGRAM_BUCKETS; col++) {	  
	  sprintf(hist_row, "<td>% 7d</td>", (int)histogram[corner][col]);
	  netconn_write(conn, hist_row, 16, NETCONN_NOCOPY);
	}
	netconn_write(conn, "</tr>", 5, NETCONN_NOCOPY);	      
      }
      netconn_write(conn, HTML_FOOTER, sizeof(HTML_FOOTER)-1, NETCONN_NOCOPY);
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
