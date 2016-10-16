Type=Service
Version=2.30
StartAtBoot=False
@EndOfDesignText@
'Service module scanner
 
Sub Process_Globals
	'These global variables will be declared once when the application starts.
	' These variables can be accessed from all modules.
	' so the UI can easily access them
	Dim connected As Boolean
	Dim first_km As Boolean
	Dim rsp As String
	Dim tmp As String
	Dim Frame As String
	Dim PID As String
	Dim Speed As Int ' kM/H
	Dim Odo As Int
	Dim Odo_prev As Int
	Dim B_SoC As Double
	Dim B_Amp As Double
	Dim B_volt As Double
	Dim B_W As Double
	Dim S_vasec_pos As Double
	Dim S_vasec_neg As Double
	Dim S_vakm_pos As Long
	Dim S_vakm_neg As Long
	Dim ctr_va_km As Int
	Dim km_nbs As Int
	Dim S_vaTrip_pos As Double
	Dim S_vaTrip_neg As Double
	Dim Trip_dist As Float
	Dim Trip_dist_prev As Float
	Dim ctr_va_trip As Int
	Dim autonomie As Int
	Dim mB As Double 
	Dim FpS As Int		' frame / sec will be used as a watchdog
	Dim I_vakm_pos As Int
	Dim I_vakm_neg As Int

	Dim wtmp As Long
	Dim Bigv As Long		' these constants are affected once
	Bigv = 256 * 128
	Dim smallv As Long
	smallv = 256
	Dim nbsh As Long
	nbsh = 3600
	Dim k1000 As Long
	k1000 = 1000
	Dim k3_6 As Long
	k3_6 = 3.6
	Dim response As StringBuilder
	Dim msg1 As String
	Dim Now As Long
	Dim Start As Int		' position de départ pour analyse de trame
	Dim Pos As Int			' curseur de décodage de trame
	Dim BB(8) As Int 		' array to store the usefull part from the frames as decimal values (0 - 255)
	Dim ptrcmd As Int
	Dim str_init(13) As String
	str_init(0) = " " 	' just for fun
	str_init(1) = "ATSP6"	 & Chr(13)	' CAN 11 bits @ 500k
	str_init(2) = "ATE0" 	 & Chr(13)	' Echo OFF
	str_init(3) = "ATH1" 	 & Chr(13)	' Header ON
	str_init(4) = "ATL0" 	 & Chr(13)	' no crlf
	str_init(5) = "ATS0" 	 & Chr(13)	' suppress spaces
	str_init(6) = "STFCP" & Chr(13)	' Clear Filters						
	str_init(7) = "STFAP 346, FFF" & Chr(13)	' put filter
	str_init(8) = "STFAP 374, FFF" & Chr(13)	' put filter
	str_init(9) = "STFAP 373, FFF" & Chr(13)	' put filter
	str_init(10) = "STFAP 412, FFF" & Chr(13)	' put filter
	str_init(11) = "STFAP 298, FFF" & Chr(13)	' put filter
	str_init(12) = "STM" & Chr(13) ' show frames
	Dim AStream As AsyncStreams
	Dim ptr As Int
	Dim cmd As String	
	Dim Timer1 As Timer
	Dim firsttime As Boolean
	Dim Start_Ticker As Long
	Dim Start_Time As Long
	Dim Trip_Distance As Long
	Dim Trip_WH_pos, Trip_WH_neg As Long
	Dim Trip_nbs As Long
	Dim GPS1 As GPS
	Dim Gps_Lat As String : Gps_Lat= "Nowhere"
	Dim Gps_Lon As String : Gps_Lon= "Nowhere"
	Dim Gps_Speed As Float
	Dim Gps_Alt As Int
	Dim Ack As Boolean
	Dim Notification1 As Notification
	Dim simul As Boolean
	Dim M_RPM As Int
	Dim dist_coef As Float
	
End Sub
 
Sub Service_Create
	Dim ps As PhoneSensors
	ps.Initialize2(ps.TYPE_PRESSURE, 2) 
	ps.StartListening("PRESSURE")
	Notification1.Initialize
	Notification1.Icon = "icon" 'use the application icon file for the notification
	Notification1.Vibrate = False
	Dim DBFilePaths As String			: DBFilePaths = File.DirRootExternal & "/BT_CAN"
	Dim DBFileNames As String			: DBFileNames = "simul.txt"
	If File.Exists(DBFilePaths, DBFileNames) = True Then
		simul = True
	Else
		simul=False
	End If
End Sub
 
Sub Service_Start (StartingIntent As Intent)

	firsttime = True
	ptr = 0
	Trip_Distance = 0
	Trip_dist = 0
	Trip_dist_prev=0
	dist_coef = 36 * Main.SPDFACT ' 57.75 conv m_rpm --> km/h , 36 conv km/h ---> m  
	ctr_va_km = 0
	ctr_va_trip = 0
	S_vasec_pos = 0
	S_vakm_pos = 0
	S_vaTrip_pos = 0
	S_vasec_neg = 0
	S_vakm_neg = 0
	S_vaTrip_neg = 0	
	Start_Time = DateTime.Now
	first_km = True
	GPS1.Initialize("GPS")
	GPS1.Start(100, 0)
	'Make sure that the process is not killed 
	'This will also show the status bar notification
	Dim n As Notification 
	n.Initialize
	n.Icon = "icon"
	n.SetInfo("canmonitor", "service actif", "Main") 
	n.Sound = False
	n.Vibrate = False
	n.Light = False
	n.OnGoingEvent = True
	Service.StartForeground(1, n)
	If AStream.IsInitialized Then AStream.Close ' In case the connection was broken and restarted
	DoEvents
	AStream.Initialize(Main.serial1.InputStream, Main.serial1.OutputStream, "AStream")
	DoEvents
	
	response.Initialize
	If simul=True Then
		ptrcmd=100
	Else
		ptrcmd=0
		send_nextcmd
	End If
	connected = True
	ToastMessageShow("Connected successfully", False)
	Ack = True
	Start_Ticker = DateTime.Now
	Timer1.Initialize("Timer1", 1000) 	' 1000 = 1 second
	Timer1.Enabled = True
	msg1 = "4 init seq started"
	CallSub(Main, "ShowConnectSts")
End Sub
 
Sub Service_Destroy
	GPS1.Stop
	' we close everything 
	AStream.Close
	Dim ps As PhoneSensors
	ps.Initialize(ps.TYPE_PRESSURE)
	ps.StopListening
End Sub
 
Sub send_nextcmd
	msg1 = "5 commande " & str_init(ptrcmd)
	CallSub(Main, "ShowConnectSts")
	Log("canion:cmd1 _" & str_init(ptrcmd) )
	AStream.Write(str_init(ptrcmd).GetBytes("UTF8"))
	If ptrcmd < 20 Then
		ptrcmd = ptrcmd + 1
	End If
End Sub
 
Sub AStream_NewData (Buffer() As Byte)
	' this event is activated when we receive data
	' we will do something only after receiving a Chr(13)
	' that means there is some food to eat
	rsp = BytesToString(Buffer, 0, Buffer.Length, "UTF8")
'		Log("canion:rsp1 _"& rsp )
	If (ptrcmd <= 12) AND (rsp.Contains(">")) Then		' we received a > , we are ready to send next command
		send_nextcmd
		response.Initialize 'clear string buffer
		Return
	End If
	response.append(rsp)
	'	Log("canion:rsp2 _"& response.ToString )
	Dim x As Int
	x = 0
	Do Until x = - 1
		tmp = response.ToString
		x = tmp.IndexOf(Chr(13))
		'Log("canion:rspx _"& x & "_"& tmp )
		If x = 19 Then ' only valid frames
			Frame = tmp.SubString2(0, x)
			decode(Frame)
			response = response.remove(0, x + 1)
		Else
			x = - 1
			response.Initialize 'clear string buffer
		End If
		DoEvents
	Loop
End Sub
 
Sub decode(msg )
	' Analysis of the response
	Select msg.SubString2(0, 1)
		Case "O"				' this is an OK , just go on
		Case "2"				' the answer is interesting
			ventile(msg)		' ventilation de la moelle dans un tableau d'entiers 
		Case "3"				' the answer is interesting
			ventile(msg)		' ventilation de la moelle dans un tableau d'entiers 
		Case "4"				' the answer is interesting
			ventile(msg)		' ventilation de la moelle dans un tableau d'entiers 	
		Case Else
			' Msgbox(msg, "réponse inattendue")
	End Select	
End Sub
 
Sub AStream_Error
	ToastMessageShow(LastException.Message, True)
	' call the police
End Sub
 
Sub ventile(msg)
	FpS = FpS + 1
	PID = msg.SubString2(0, 3)
	Start = 3
	For I = 0 To 7
		Pos = Start + I * 2		
		BB(I) = Bit.ParseInt(msg.substring2(Pos, Pos + 2), 16) 'transform 2 hexbytes in one integer
	Next
	Select PID
		Case("298")			' 10 / sec	
		M_RPM = BB(6)*256+BB(7) -10000
		Trip_dist=Trip_dist+ (M_RPM / dist_coef) ' meters
		
		Case("346")			' 50 / sec
		autonomie = BB(7)
		
		Case("373")			' 100 / sec
		B_Amp = (BB(2) * 256 + BB(3) - Bigv )/100
		B_volt = (BB(4) * 256 + BB(5))/10
		B_W = B_Amp * B_volt
		ctr_va_km = ctr_va_km + 1
		ctr_va_trip = ctr_va_trip + 1
		If (B_W > 0) Then
			S_vasec_pos = S_vasec_pos + B_W
			S_vakm_pos = S_vakm_pos + B_W
			S_vaTrip_pos = S_vaTrip_pos + B_W
		Else 
			S_vasec_neg = S_vasec_neg + B_W
			S_vakm_neg = S_vakm_neg + B_W
			S_vaTrip_neg = S_vaTrip_neg + B_W
		End If
		
		Case("374")			' 10 / sec	
		B_SoC = (BB(1) - 10)/2
		
		Case("412")			' 10 / sec
		Speed = BB(1)
		If Speed > 200 Then
			Speed = Speed - 255
		End If
		Odo = (BB(2) * 256 + BB(3)) * 256 + BB(4)
		CallSub(Main, "RefreshFast")
		If first_km = True Then 
			Odo_prev = Odo
			first_km = False
		End If
		If Odo > Odo_prev Then	 
			Trip_Distance = Trip_Distance + 1
			wtmp = S_vakm_pos/360000
			I_vakm_pos = wtmp
			wtmp = S_vakm_neg/360000
			I_vakm_neg = wtmp			
			
			
			'adjust dist_coef after 2 kms
			Dim ecart As Int
			ecart = Trip_dist - Trip_dist_prev 'should be 1000 meter
			If Trip_Distance > 2 Then
				dist_coef = dist_coef / (1000 / ecart)
				' Log("correction: " & Trip_dist &TAB &Trip_dist_prev & TAB &dist_coef)
			End If
			Trip_dist_prev = Trip_dist
			
			CallSub(Main, "RefreshOdo")			' update km
			
			Odo_prev = Odo
			S_vakm_neg = 0
			S_vakm_pos = 0
			ctr_va_km = 0
			km_nbs = 0
		End If
		Case Else
	End Select
	DoEvents
End Sub
 
Sub Timer1_tick ' every second
	Trip_nbs = Trip_nbs + 1
	km_nbs = km_nbs + 1
	Trip_WH_pos = S_vaTrip_pos/360000 'integration VA à raison de 100 captures /sec
	Trip_WH_neg = S_vaTrip_neg/360000 'integration VA à raison de 100 captures /sec
	CallSub(Main, "refreshsec")
	CallSub(Main, "refreshgps")
	S_vasec_neg = 0
	S_vasec_pos = 0 
	FpS = 0
End Sub
'Sub Sleep(ms As Long)
'	If ms > 1000 Then ms = 1000 'avoid application not responding error
'	DatHeur = DateTime.Now
'	Do Until (DateTime.Now > DatHeur + ms)
'		DoEvents
'	Loop
'End Sub
 
Sub PRESSURE_SensorChanged(Values() As Float)
	mB = (mB * 4 + Values(0)) / 5 ' smoothing 
End Sub
 
Sub GPS_LocationChanged (Location1 As Location)
'	Gps_Lat = Location1.ConvertToMinutes(Location1.Latitude)
'	Gps_Lon = Location1.ConvertToMinutes(Location1.Longitude)
	Gps_Lat = Location1.Latitude
	Gps_Lon = Location1.Longitude
	Gps_Speed = Location1.Speed * 3.6 ' convert m/s to km/h
	Gps_Alt = Location1.Altitude
	
	'CallSub(Main, "refreshgps")
End Sub