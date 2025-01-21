behavior_name=goto_list
# Written by SFMC on UTC: 2022-11-08T13:22:56.386096
# goto_l10.ma
# updated for start of NoSE 2025 mission nose.mi

<start:b_arg>
	b_arg: num_legs_to_run(nodim) -1
	b_arg: start_when(enum) 0 # BAW_IMMEDIATELY
	b_arg: list_stop_when(enum) 7 # BAW_WHEN_WPT_DIST
	b_arg: initial_wpt(enum) -1 # One after last achieved
	b_arg: num_waypoints(nodim) 6
	b_arg: list_when_wpt_dist(m) 100               #! min = 10.0
                                                   # used if list_stop_when == 7
<end:b_arg>
<start:waypoints>
138.10  6244.05
054.00	6224.00
126.06  6204.18 # guide 1 to wpt 2 
217.01  6134.49 # guide 2 to wpt 2
245.00	6115.00 # MAIN wpt 2 enter channel
336.00	6106.00 # MAIN wpt 3 inside channel
<end:waypoints>
