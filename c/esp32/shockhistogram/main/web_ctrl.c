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

const static char HEADER[] = "HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n";
const static char HTML_RESULT[] =
  "<!DOCTYPE html><html><head> <title>Racepi Shock Histogrammer</title> </head>\n"
  "<body>\n"
  "<h1>Shock histograms forthcoming</h1>\n"
  "</body></html>\n";

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
      netconn_write(conn, HEADER, sizeof(HEADER)-1, NETCONN_NOCOPY);
      netconn_write(conn, HTML_RESULT, sizeof(HTML_RESULT)-1, NETCONN_NOCOPY);
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
