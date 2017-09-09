# RetroPie-rsync-Monitor

rsync Monitor will monitor the process list on the raspberry pi and detect when RetroPie is copying ROMs from the external storage drive. It will flash LED(s) connected to GPIO pin # 8 (change to whichever pin you prefer in the .py file). Giving you a visual indication when RetroPie is copying ROMs.

Download rsync_monitor.py anywhere on your Raspberry Pi
Open/Edit the file (in terminal: nano rsync_monitor.py) and change the 
 
> led_pin = 8

To whichever pin you're using for the LEDs.

Save the file and run
> sudo python rsync_monitor.py

Or have the script started on boot
> sudo nano /etc/rc.local

And add this line just above exit 0
> python /path_to_the_file/rsync_monitor.py &
