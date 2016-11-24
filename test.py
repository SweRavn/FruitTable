import xy_table

with xy_table.Xy_table(x_motor_id = 1,
              x_steps_per_rev = 200,
              y_steps_per_rev = 200,
#              x_stepping = xy_table.MICROSTEP,
#              y_stepping = xy_table.MICROSTEP,
              x_stepping = xy_table.SINGLE,
              y_stepping = xy_table.SINGLE,
              x_speed = 240,
              y_speed = 240,
              boundary_check = True,
              x_thread_pitch = 0.001,
              y_thread_pitch = 0.001,
              x_length_m = 0.134,
              y_length_m = 0.046,
              async = False) as tbl:

    n = 0
#    while True:
#        tbl.move_steps(1000, 0)
#        tbl.move(0, 100)
#        n += 1
#        print(n*1000)
    tbl.move_steps(1000, 0)
