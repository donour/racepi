#include "dl1.h"
#include "tests.h"

void test_sends(BluetoothSerial *port) { 
  dl1_message_t dl1_message;


  if ( ! get_speed_message(&dl1_message, (millis()/10) % 200, 10)) {
    send_dl1_message(&dl1_message, port, true);
  }

  if ( ! get_gps_pos_message(&dl1_message, 41000000, 3400000, 1200)) {
    send_dl1_message(&dl1_message, port, true);
  }

  if ( ! get_tps_message(&dl1_message, (millis()/100) % 101)) {
    send_dl1_message(&dl1_message, port, true);
  }

  if ( ! get_rpm_message(&dl1_message,  sin(millis()/3000.0)*4500 + 4500)) {
    send_dl1_message(&dl1_message, port, true);
  }  

  if ( ! get_steering_angle_message(&dl1_message, sin(millis()/3000.0)*200)){
    send_dl1_message(&dl1_message, port, true);
  }  

  if ( ! get_xy_accel_message(&dl1_message, sin(millis()/3000.0)/1.1, cos(millis()/3000.0)/1.1)) {
    send_dl1_message(&dl1_message, port, true);
  }    
}
