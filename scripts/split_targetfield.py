import os
import sys
import datetime

target = sys.argv[3]#important, not 0!
frbtime = sys.argv[4]
directory = 'processing/'+str(sys.argv[5])+'/'
secondday = sys.argv[6]
print(target, frbtime,directory,secondday)

try:
        os.system("rm -fr %sfrbfield.ms" % directory)
except:
        print('No previous file existed')

frb_time = datetime.datetime.strptime(frbtime,"%H:%M:%S")
frb_time = frb_time.replace(year=datetime.datetime.today().year) #for edge case of just after midnight - else tries to go from 1900 to 1899 which breaks things
timestart = frb_time - datetime.timedelta(minutes = 7.5)
timeend = frb_time + datetime.timedelta(minutes = 7.5)

default(split)
#try to split. if the time is on a second day of observation, then we need to try adding 24 hours
if secondday == False or secondday == 'False':
	print('First day')
	#split(vis=target, outputvis=directory+"frbfield.ms", timerange=timestart.strftime("%H:%M:%S")+"~"+timeend.strftime("%H:%M:%S"), datacolumn='all')
	split(vis=target, outputvis=directory+"frbfield.ms", datacolumn='all')
else:
	#first, look for the edge case. I.E. FRB on first day within 7.5 min of midnight, second day within 7.5 min of midnight
	#third case is easier "second day, not just after midnight"
	print('Trying for when time is on a 2nd day of observing... or close to it')
	timesplit = frbtime.split(':')
	if int(timesplit[0])==23 and (int(timesplit[1])>52 or (int(timesplit[1])==52 and int(timesplit[2])>=30)):
		#timest = timestart.strftime("%H:%M:%S").split(':')
                #newtimestart = '%s:%s:%s' % (str(int(timest[0])+24),timest[1],timest[2])
                timeen = timeend.strftime("%H:%M:%S").split(':')
                newtimeend = '%s:%s:%s' % (str(int(timeen[0])+24),timeen[1],timeen[2])
                split(vis=target, outputvis=directory+"frbfield.ms", timerange=timestart.strftime("%H:%M:%S")+"~"+newtimeend,datacolumn='all')
	elif int(timesplit[0])==0 and (int(timesplit[1])<7 or (int(timesplit[1])==7 and int(timesplit[2])<=30)):
		#timest = timestart.strftime("%H:%M:%S").split(':')
                #newtimestart = '%s:%s:%s' % (str(int(timest[0])+24),timest[1],timest[2])
                timeen = timeend.strftime("%H:%M:%S").split(':')
                newtimeend = '%s:%s:%s' % (str(int(timeen[0])+24),timeen[1],timeen[2])
                split(vis=target, outputvis=directory+"frbfield.ms", timerange=timestart.strftime("%H:%M:%S")+"~"+newtimeend,datacolumn='all')
	else:
		try:
			timest = timestart.strftime("%H:%M:%S").split(':')
			newtimestart = '%s:%s:%s' % (str(int(timest[0])+24),timest[1],timest[2])
			timeen = timeend.strftime("%H:%M:%S").split(':')
                	newtimeend = '%s:%s:%s' % (str(int(timeen[0])+24),timeen[1],timeen[2])
			split(vis=target, outputvis=directory+"frbfield.ms", timerange=newtimestart+"~"+newtimeend,datacolumn='all')
		except:
			#implement edge cases here for when the time is just after midnight, or just before!
			print("Time doesn't work!")
#split(vis=target, outputvis="frbfield.ms", timerange='26:14:03.414~26:29:03.414', datacolumn='all')
#split(vis='scienceData.ASKAP_Filming_MW.SB30149.ASKAP_Filming_MW.beam02_averaged.ms', outputvis='test2.ms', timerange='15:47:58~15:48:28', datacolumn='all')
